#!/usr/bin/env python3
"""Navix Livre: servidor MCP local Windows, sem pacotes pagos."""
import argparse
import base64
import ctypes
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import urllib.parse
import webbrowser

VERSION="0.3.0"
def desktop():
    if os.name=="nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as h:
                value,_=winreg.QueryValueEx(h,"Desktop")
            p=Path(os.path.expandvars(value))
            if p.is_dir(): return p.resolve()
        except OSError: pass
    return (Path.home()/"Desktop").resolve()

def flag(key): return os.getenv(key,"").lower() in ("1","true","sim","yes")

class Agent:
    def __init__(self,roots=None,write=None,commands=None,ui=None):
        self.desktop=desktop()
        raw=os.getenv("NAVIX_ALLOWED_DIRS")
        self.roots=[Path(p).expanduser().resolve() for p in
                    (roots if roots is not None else (raw.split(os.pathsep) if raw else [self.desktop]))]
        self.write=flag("NAVIX_ALLOW_WRITE") if write is None else write
        self.commands=flag("NAVIX_ALLOW_COMMANDS") if commands is None else commands
        self.ui=flag("NAVIX_ALLOW_UI") if ui is None else ui
    def safe(self,path=None):
        p=Path(path or self.desktop).expanduser().resolve()
        if not any(p==r or r in p.parents for r in self.roots):
            raise PermissionError("Fora das pastas autorizadas")
        return p
    def status(self):
        return dict(nome="Navix Livre",versao=VERSION,computador=platform.node(),
                    sistema=platform.platform(),desktop=str(self.desktop),
                    pastas=[str(r) for r in self.roots],escrita=self.write,
                    terminal=self.commands,controle_visual=self.ui,rede="rede publica fechada; ponte local opcional")
    def list_directory(self,path=None):
        p=self.safe(path)
        if not p.is_dir(): raise NotADirectoryError(str(p))
        out=[]
        items=sorted(p.iterdir(),key=lambda x:x.name.casefold())
        for item in items[:500]:
            try:
                q=self.safe(item)
                out.append(dict(nome=item.name,pasta=q.is_dir()))
            except PermissionError: out.append(dict(nome=item.name,restrito=True))
        return dict(caminho=str(p),arquivos=out,truncado=len(items)>500)
    def search_files(self,path=None,term="",limit=50):
        p=self.safe(path)
        if not p.is_dir(): raise NotADirectoryError(str(p))
        limit=max(1,min(100,int(limit)))
        hits=[]
        visited=0
        quota=30000  # evita varrer um HD inteiro num PC de poucos recursos
        for root,dirs,files in os.walk(p,followlinks=False):
            current=Path(root)
            try:
                self.safe(current)
            except PermissionError:
                dirs.clear()
                continue
            dirs[:]=[d for d in dirs if not (current/d).is_symlink()
                     and (current/d).resolve().is_relative_to(p)]
            for name in dirs+files:
                visited+=1
                if visited>quota:
                    return dict(resultados=hits,limite=True,motivo="limite de varredura")
                if term.casefold() in name.casefold():
                    try: hits.append(str(self.safe(Path(root)/name)))
                    except PermissionError: continue
                    if len(hits)>=limit: return dict(resultados=hits,limite=True)
        return dict(resultados=hits,limite=False)
    def read_text(self,path):
        p=self.safe(path)
        # Leitura limitada de verdade, mesmo se o arquivo aumentar após stat().
        with p.open("rb") as handle:
            raw=handle.read(1_000_001)
        if len(raw)>1_000_000: raise ValueError("Arquivo maior que 1MB")
        try: value=raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Arquivo nao e texto UTF-8") from exc
        if "\x00" in value: raise ValueError("Arquivo binario nao suportado")
        return dict(arquivo=str(p),texto=value)
    def write_text(self,path,text):
        if not self.write: raise PermissionError("Ative NAVIX_ALLOW_WRITE=1")
        if len(text.encode("utf-8"))>1_000_000: raise ValueError("Texto maior que 1MB")
        p=self.safe(path)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(text,encoding="utf-8")
        return dict(salvo=str(p))
    def get_file_info(self,path):
        p=self.safe(path)
        st=p.stat()
        return dict(caminho=str(p),nome=p.name,pasta=p.is_dir(),
                    tamanho_bytes=st.st_size,modificado_em=st.st_mtime)

    def create_directory(self,path):
        if not self.write: raise PermissionError("Ative NAVIX_ALLOW_WRITE=1")
        p=self.safe(path)
        p.mkdir(parents=True,exist_ok=False)
        return dict(criado=str(p))

    def move_file(self,source,destination):
        if not self.write: raise PermissionError("Ative NAVIX_ALLOW_WRITE=1")
        a=self.safe(source)
        b=self.safe(destination)
        if a==b: raise ValueError("Origem e destino iguais")
        if a.is_dir() and a in b.parents:
            raise ValueError("Nao mover uma pasta para dentro dela mesma")
        if b.exists(): raise FileExistsError("Destino ja existe")
        if not b.parent.is_dir(): raise FileNotFoundError("Pasta de destino inexistente")
        a.rename(b)
        return dict(origem=str(a),destino=str(b))

    def list_processes(self):
        if os.name!="nt": raise RuntimeError("Disponivel apenas no Windows")
        import csv
        import io
        r=subprocess.run(["tasklist.exe","/fo","csv","/nh"],capture_output=True,
                         text=True,errors="replace",timeout=12,
                         creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if r.returncode: raise RuntimeError(r.stderr[:500])
        processes=[]
        for row in csv.reader(io.StringIO(r.stdout)):
            if len(row)>=5 and row[1].isdigit():
                processes.append(dict(nome=row[0],pid=int(row[1]),memoria=row[4]))
            if len(processes)>=400: break
        return dict(processos=processes,truncado=len(processes)>=400)

    def run_command(self,command,shell="powershell",timeout=15):
        if not self.commands: raise PermissionError("Ative NAVIX_ALLOW_COMMANDS=1")
        if os.name!="nt": raise RuntimeError("Comandos locais para Windows")
        if shell=="powershell": cmd=["powershell.exe","-NoProfile","-NonInteractive","-Command",command]
        elif shell=="cmd": cmd=["cmd.exe","/D","/C",command]
        else: raise ValueError("Use powershell ou cmd")
        r=subprocess.run(cmd,capture_output=True,text=True,errors="replace",
                         stdin=subprocess.DEVNULL,timeout=max(1,min(30,int(timeout))),
                         creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        return dict(codigo=r.returncode,saida=r.stdout[:20000],erros=r.stderr[:10000])
    def open_url(self,url):
        if not self.ui: raise PermissionError("Ative NAVIX_ALLOW_UI=1")
        u=urllib.parse.urlsplit(url)
        if u.scheme not in ("http","https") or not u.hostname: raise ValueError("URL invalida")
        return dict(abertura_solicitada=url,aceito=webbrowser.open(url))
    def open_path(self,path):
        if not self.ui: raise PermissionError("Ative NAVIX_ALLOW_UI=1")
        if os.name!="nt": raise RuntimeError("Windows necessario")
        p=self.safe(path)
        os.startfile(str(p))
        return dict(aberto=str(p))
    def click(self,x,y,button="left"):
        if not self.ui: raise PermissionError("Ative NAVIX_ALLOW_UI=1")
        if os.name!="nt": raise RuntimeError("Windows necessario")
        x,y=int(x),int(y)
        if min(x,y)<0 or max(x,y)>20000: raise ValueError("Coordenadas invalidas")
        if button not in ("left","right"): raise ValueError("Botao invalido")
        u=ctypes.windll.user32
        if not u.SetCursorPos(x,y): raise OSError("Nao moveu o mouse")
        d,e=(2,4) if button=="left" else (8,16)
        u.mouse_event(d,0,0,0,0); u.mouse_event(e,0,0,0,0)
        return dict(clique=[x,y],botao=button)
    def screenshot(self):
        if not self.ui: raise PermissionError("Ative NAVIX_ALLOW_UI=1")
        if os.name!="nt": raise RuntimeError("Windows necessario")
        fd,filename=tempfile.mkstemp(prefix="navix_",suffix=".png");os.close(fd)
        p=Path(filename)
        escaped=filename.replace("'","''")
        ps=("Add-Type -AssemblyName System.Windows.Forms;Add-Type -AssemblyName System.Drawing;"
            "$r=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
            "$b=New-Object System.Drawing.Bitmap($r.Width,$r.Height);"
            "$g=[System.Drawing.Graphics]::FromImage($b);"
            "try{$g.CopyFromScreen($r.Location,[System.Drawing.Point]::Empty,$r.Size);"
            "$b.Save('"+escaped+"',[System.Drawing.Imaging.ImageFormat]::Png)}"
            "finally{$g.Dispose();$b.Dispose()}")
        try:
            r=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",ps],
                             capture_output=True,text=True,timeout=15)
            if r.returncode: raise RuntimeError(r.stderr[:500])
            b=p.read_bytes()
            if len(b)>6_000_000: raise ValueError("Imagem maior que 6MB")
            return {"content":[{"type":"image","mimeType":"image/png",
                                "data":base64.b64encode(b).decode("ascii")}]}
        finally: p.unlink(missing_ok=True)

SPECS=[
 ("status","Informacoes do agente",{},[]),
 ("get_file_info","Consulta metadados de arquivo",{"path":"string"},["path"]),
 ("list_processes","Lista processos Windows sem alterar",{},[]),
 ("create_directory","Cria pasta (autorizacao de escrita)",{"path":"string"},["path"]),
 ("move_file","Move arquivo ou pasta (autorizacao de escrita)",{"source":"string","destination":"string"},["source","destination"]),
 ("list_directory","Lista pasta autorizada",{"path":"string"},[]),
 ("search_files","Busca arquivos pelo nome",{"path":"string","term":"string","limit":"integer"},[]),
 ("read_text","Le arquivo de texto",{"path":"string"},["path"]),
 ("write_text","Escreve arquivo, opcional",{"path":"string","text":"string"},["path","text"]),
 ("run_command","PowerShell ou CMD, opcional",{"command":"string","shell":"string","timeout":"integer"},["command"]),
 ("open_url","Abre navegador, opcional",{"url":"string"},["url"]),
 ("open_path","Abre arquivo/pasta, opcional",{"path":"string"},["path"]),
 ("click","Clica no mouse, opcional",{"x":"integer","y":"integer","button":"string"},["x","y"]),
 ("screenshot","Captura a tela, opcional",{},[])
]
def tools():
    return [dict(name=n,description=d,inputSchema=dict(type="object",
            properties={k:{"type":v} for k,v in p.items()},
            required=req,additionalProperties=False)) for n,d,p,req in SPECS]
def call(agent,name,args):
    if name not in {n for n,_,_,_ in SPECS}: raise ValueError("Ferramenta desconhecida")
    value=getattr(agent,name)(**args)
    if name=="screenshot": return value
    return {"content":[{"type":"text","text":json.dumps(value,ensure_ascii=False)}]}

def mcp(agent):
    for line in sys.stdin:
        request=None
        try:
            request=json.loads(line)
            if not isinstance(request,dict) or "id" not in request: continue
            method=request.get("method")
            if method=="initialize":
                v=(request.get("params") or {}).get("protocolVersion","2024-11-05")
                result=dict(protocolVersion=v if v in ("2024-11-05","2025-03-26","2025-06-18") else "2024-11-05",
                            capabilities={"tools":{}},serverInfo={"name":"navix-livre","version":VERSION})
            elif method=="tools/list": result={"tools":tools()}
            elif method=="ping": result={}
            elif method=="tools/call":
                p=request.get("params") or {}
                try: result=call(agent,p.get("name"),p.get("arguments") or {})
                except Exception as e:
                    result={"content":[{"type":"text","text":type(e).__name__+": "+str(e)}],
                            "isError":True}
            else: raise NotImplementedError(str(method))
            answer={"jsonrpc":"2.0","id":request["id"],"result":result}
        except Exception as e:
            answer={"jsonrpc":"2.0","id":request.get("id") if isinstance(request,dict) else None,
                    "error":{"code":-32603,"message":str(e)}}
        sys.stdout.write(json.dumps(answer,ensure_ascii=False)+"\n");sys.stdout.flush()

def gui_classic(agent):
    import tkinter as tk
    from tkinter import scrolledtext,messagebox
    win=tk.Tk();win.title("Navix Livre | Controle Local");win.geometry("760x500")
    tk.Label(win,text="NAVIX LIVRE • Gratuito",font=("Segoe UI",18,"bold")).pack(pady=12)
    tk.Label(win,text=str(agent.desktop),wraplength=720).pack()
    output=scrolledtext.ScrolledText(win);output.pack(fill="both",expand=True,padx=16,pady=12)
    def show(data):
        output.delete("1.0","end")
        output.insert("end",json.dumps(data,ensure_ascii=False,indent=2))
    def listing():
        try: show(agent.list_directory())
        except Exception as e: messagebox.showerror("Erro",str(e))
    def open_desktop():
        try:
            if os.name=="nt": os.startfile(str(agent.desktop))
        except Exception as e: messagebox.showerror("Erro",str(e))
    bridge=[None]
    def start_bridge():
        try:
            proc=bridge[0]
            if proc is not None and proc.poll() is None:
                messagebox.showinfo("Navix Livre","Conexao MCP local ja iniciada.")
                return
            if getattr(sys,"frozen",False):
                executable=Path(sys.executable).with_name("NavixBridge.exe")
                if not executable.is_file():
                    raise FileNotFoundError("NavixBridge.exe nao encontrado na pasta do programa")
                argv=[str(executable)]
            else:
                script=Path(__file__).with_name("navix_remote.py")
                if not script.is_file():
                    raise FileNotFoundError("navix_remote.py nao encontrado")
                argv=[sys.executable,str(script)]
            bridge[0]=subprocess.Popen(argv,cwd=str(Path(argv[-1]).parent),
                creationflags=getattr(subprocess,"CREATE_NEW_CONSOLE",0))
            messagebox.showinfo("Ponte MCP local iniciada",
                "Porta: 127.0.0.1:8765. Somente no proprio computador.\n"
                "Para parar, use o botao Parar ou feche a janela da ponte.\n"
                "Isso nao conecta automaticamente a conversa do ChatGPT.")
        except Exception as exc:
            messagebox.showerror("Erro ao iniciar ponte",str(exc))

    def stop_bridge():
        proc=bridge[0]
        if proc is not None and proc.poll() is None:
            proc.terminate()
            bridge[0]=None
            messagebox.showinfo("Navix Livre","Conexao MCP local encerrada.")
        else:
            messagebox.showinfo("Navix Livre",
                "Nenhuma ponte iniciada por este painel.\n"
                "Se abriu pelo Menu Iniciar, feche a janela Conexao MCP local.")

    bar=tk.Frame(win);bar.pack(pady=6)
    tk.Button(bar,text="Listar Area de Trabalho",command=listing).pack(side="left",padx=6)
    tk.Button(bar,text="Abrir Area de Trabalho",command=open_desktop).pack(side="left",padx=6)
    tk.Button(bar,text="Diagnostico",command=lambda:show(agent.status())).pack(side="left",padx=6)
    remote=tk.Frame(win);remote.pack(pady=4)
    tk.Button(remote,text="Iniciar conexao MCP local",command=start_bridge).pack(side="left",padx=6)
    tk.Button(remote,text="Parar conexao MCP local",command=stop_bridge).pack(side="left",padx=6)
    tk.Label(win,text="Conexao externa com ChatGPT exige configuracao adicional.",
             fg="#6c2828").pack(pady=(2,8))
    show(agent.status());win.mainloop()

def gui(agent):
    from navix_gui import run_gui
    return run_gui(agent)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mcp",action="store_true")
    ap.add_argument("--gui",action="store_true")
    ap.add_argument("--doctor",action="store_true")
    a=ap.parse_args();agent=Agent()
    if a.mcp: mcp(agent)
    elif a.gui or (not a.doctor and getattr(sys,"frozen",False)): gui(agent)
    else: print(json.dumps(agent.status(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()

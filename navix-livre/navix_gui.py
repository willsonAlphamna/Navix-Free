"""Navix Livre — interface Windows moderna, sem bibliotecas pagas."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

BG="#0c121a"
PANEL="#111a25"
PANEL2="#172334"
SIDE="#101a27"
LINE="#2a3a4c"
TEXT="#e7edf6"
MUTED="#a0b0c1"
BLUE="#1671d9"
BTN="#253348"
GREEN="#25c57a"
RED="#ff8080"

class NavixWindow:
    def __init__(self,agent):
        self.agent=agent
        self.root=tk.Tk()
        self.root.title("Navix Livre | Controle do computador")
        self.root.geometry("1230x760")
        self.root.minsize(890,590)
        self.root.configure(bg=BG)
        try:
            resource=Path(getattr(sys,"_MEIPASS",Path(__file__).parent))/"navix.ico"
            if resource.is_file(): self.root.iconbitmap(default=str(resource))
        except (OSError,tk.TclError): pass
        self.bridge=None
        self.location=agent.desktop
        self.records={}
        self.mode="Arquivos"
        self.build()
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.show_folder(self.location)
        self.root.after(1200,self.check_bridge)

    def label(self,parent,text="",size=10,fg=TEXT,bg=None,bold=False,**kw):
        return tk.Label(parent,text=text,fg=fg,bg=bg or parent.cget("bg"),
                        font=("Segoe UI",size,"bold" if bold else "normal"),**kw)

    def button(self,parent,text,cmd,primary=False,enabled=True,**kw):
        b=tk.Button(parent,text=text,command=cmd,bg=BLUE if primary else BTN,
                    fg="white" if enabled else MUTED,activebackground="#3167a8",
                    activeforeground="white",relief="flat",bd=0,
                    font=("Segoe UI",10),padx=11,pady=9,cursor="hand2",
                    state="normal" if enabled else "disabled",**kw)
        return b

    def build(self):
        header=tk.Frame(self.root,bg=PANEL,height=73)
        header.pack(fill="x")
        header.pack_propagate(False)
        emblem=tk.Canvas(header,width=44,height=44,bg=PANEL,highlightthickness=0)
        emblem.pack(side="left",padx=(20,12),pady=13)
        emblem.create_rectangle(2,2,42,42,fill=BLUE,outline="",width=0)
        emblem.create_text(22,22,text="✒",fill="white",font=("Segoe UI Symbol",23,"bold"))
        htext=tk.Frame(header,bg=PANEL)
        htext.pack(side="left")
        self.label(htext,"Navix Livre",19,bold=True,bg=PANEL).pack(anchor="w")
        self.label(htext,"Gerenciamento local gratuito para Windows",9,fg=MUTED,bg=PANEL).pack(anchor="w")
        self.connection=self.label(header,"●  Ponte local desligada",10,fg=MUTED,bg=PANEL)
        self.connection.pack(side="right",padx=23)

        content=tk.Frame(self.root,bg=BG)
        content.pack(fill="both",expand=True)
        self.sidebar=tk.Frame(content,bg=SIDE,width=213)
        self.sidebar.pack(side="left",fill="y")
        self.sidebar.pack_propagate(False)
        self.nav={}
        for title,symbol in [
            ("Arquivos","▣"),("Terminal",">_"),("Processos","≡"),
            ("Captura de Tela","▧"),("Comandos","</>"),
            ("Configurações","⚙"),("Sobre","ⓘ")]:
            b=tk.Button(self.sidebar,text="  "+symbol+"   "+title,anchor="w",
                        bg=SIDE,fg=TEXT,activebackground=BLUE,activeforeground="white",
                        relief="flat",bd=0,font=("Segoe UI",11),
                        padx=12,pady=13,cursor="hand2",
                        command=lambda section=title:self.navigate(section))
            b.pack(fill="x",padx=9,pady=(5,0))
            self.nav[title]=b
        self.label(self.sidebar,"LOCAL • SEM MENSALIDADE",8,fg=MUTED,bg=SIDE).pack(side="bottom",pady=18)

        center=tk.Frame(content,bg=BG)
        center.pack(side="left",fill="both",expand=True)
        self.body=tk.Frame(center,bg=BG)
        self.body.pack(fill="both",expand=True)
        bottom=tk.Frame(center,bg=PANEL,height=34)
        bottom.pack(fill="x",side="bottom")
        bottom.pack_propagate(False)
        self.status=self.label(bottom,"Pronto",9,bg=PANEL,fg=MUTED)
        self.status.pack(side="left",padx=16)
        self.label(bottom,"Navix Livre 0.3 • Acesso local",9,bg=PANEL,fg=MUTED).pack(side="right",padx=14)
        self.navigate("Arquivos")

    def navigate(self,section):
        self.mode=section
        for name,b in self.nav.items():
            b.configure(bg=BLUE if name==section else SIDE)
        for child in self.body.winfo_children():
            child.destroy()
        if section=="Arquivos": self.build_files()
        elif section=="Terminal": self.build_terminal()
        elif section=="Processos": self.build_processes()
        elif section=="Captura de Tela": self.build_capture()
        elif section=="Comandos": self.build_commands()
        elif section=="Configurações": self.build_settings()
        else: self.build_about()

    def title(self,value,subtitle):
        bar=tk.Frame(self.body,bg=BG)
        bar.pack(fill="x",padx=18,pady=(18,9))
        self.label(bar,value,17,bold=True).pack(anchor="w")
        self.label(bar,subtitle,10,fg=MUTED).pack(anchor="w")

    def build_files(self):
        ribbon=tk.Frame(self.body,bg=BG)
        ribbon.pack(fill="x",padx=16,pady=(15,6))
        self.button(ribbon,"←",self.back).pack(side="left",padx=(0,5))
        self.button(ribbon,"Início",lambda:self.show_folder(self.agent.desktop)).pack(side="left",padx=(0,9))
        self.path_var=tk.StringVar(value=str(self.location))
        self.path_box=tk.Entry(ribbon,textvariable=self.path_var,fg=TEXT,bg=PANEL,
                    insertbackground=TEXT,relief="flat",font=("Segoe UI",10))
        self.path_box.pack(side="left",fill="x",expand=True,ipady=10)
        self.path_box.bind("<Return>",lambda _:self.show_folder(self.path_var.get()))
        self.button(ribbon,"Ir",lambda:self.show_folder(self.path_var.get())).pack(side="left",padx=(6,10))
        self.search_var=tk.StringVar()
        find=tk.Entry(ribbon,textvariable=self.search_var,fg=TEXT,bg=PANEL,
                        insertbackground=TEXT,relief="flat",font=("Segoe UI",10),width=18)
        find.pack(side="left",ipady=10)
        find.insert(0,"")
        find.bind("<Return>",lambda _:self.search())
        self.button(ribbon,"Buscar",self.search).pack(side="left",padx=(6,0))

        actions=tk.Frame(self.body,bg=BG)
        actions.pack(fill="x",padx=16,pady=(1,8))
        self.button(actions,"Nova pasta",self.new_folder,enabled=self.agent.write).pack(side="left",padx=(0,6))
        self.button(actions,"Importar",self.import_file,enabled=self.agent.write).pack(side="left",padx=6)
        self.button(actions,"Exportar",self.export_file).pack(side="left",padx=6)
        self.button(actions,"Abrir",self.open_selected).pack(side="left",padx=6)
        self.button(actions,"Renomear",self.rename_selected,enabled=self.agent.write).pack(side="left",padx=6)
        self.button(actions,"Excluir",self.delete_selected,enabled=self.agent.write).pack(side="left",padx=6)
        self.button(actions,"Atualizar",lambda:self.show_folder(self.location)).pack(side="left",padx=6)

        area=tk.Frame(self.body,bg=BG)
        area.pack(fill="both",expand=True,padx=16,pady=(0,9))
        listing=tk.Frame(area,bg=PANEL)
        listing.pack(side="left",fill="both",expand=True)
        self.details=tk.Frame(area,bg=PANEL,width=224)
        self.details.pack(side="right",fill="y",padx=(10,0))
        self.details.pack_propagate(False)
        style=ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Navix.Treeview",background=PANEL,fieldbackground=PANEL,
                        foreground=TEXT,rowheight=29,borderwidth=0,font=("Segoe UI",10))
        style.configure("Navix.Treeview.Heading",background=PANEL2,foreground=TEXT,
                        relief="flat",font=("Segoe UI",10,"bold"))
        style.map("Navix.Treeview",background=[("selected","#174d90")],
                  foreground=[("selected","white")])
        cols=("tipo","tamanho","data")
        self.tree=ttk.Treeview(listing,columns=cols,show="tree headings",
                               style="Navix.Treeview",selectmode="browse")
        self.tree.heading("#0",text="Nome")
        self.tree.heading("tipo",text="Tipo")
        self.tree.heading("tamanho",text="Tamanho")
        self.tree.heading("data",text="Modificado")
        self.tree.column("#0",minwidth=155,width=275,stretch=True)
        self.tree.column("tipo",minwidth=70,width=105,stretch=False)
        self.tree.column("tamanho",minwidth=70,width=80,stretch=False)
        self.tree.column("data",minwidth=115,width=135,stretch=False)
        scroll=ttk.Scrollbar(listing,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        self.tree.bind("<<TreeviewSelect>>",self.selected_details)
        self.tree.bind("<Double-1>",lambda _:self.open_selected())
        self.console=tk.Text(self.body,height=6,bg="#080e14",fg="#e0e8f3",
                             insertbackground=TEXT,relief="flat",
                             font=("Consolas",10),wrap="word",state="disabled")
        self.console.pack(fill="x",padx=16,pady=(0,11))
        self.append("Navix Livre iniciado. Navegação limitada às pastas autorizadas.")
        self.render_details(None)

    def append(self,text):
        if not hasattr(self,"console") or not self.console.winfo_exists(): return
        self.console.configure(state="normal")
        self.console.insert("end",str(text)+"\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def notify(self,message):
        self.status.configure(text=str(message)[:155])
        if self.mode=="Arquivos": self.append(message)

    def error(self,exc):
        self.notify("Erro: "+str(exc))
        messagebox.showerror("Navix Livre",str(exc),parent=self.root)

    def show_folder(self,path):
        if self.mode!="Arquivos": return
        try:
            p=self.agent.safe(path)
            result=self.agent.list_directory(str(p))
            self.location=p
            self.path_var.set(str(p))
            self.tree.delete(*self.tree.get_children())
            self.tree.heading("data",text="Modificado")
            self.records={}
            for item in result["arquivos"]:
                child=p/item["nome"]
                if item.get("restrito"): continue
                folder=item["pasta"]
                try:
                    stat=child.stat()
                    size="—" if folder else self.hsize(stat.st_size)
                    date=dt.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                except OSError:
                    size="—";date="—"
                iid=self.tree.insert("",tk.END,text=("📁 " if folder else "▤ ")+item["nome"],
                                     values=("Pasta" if folder else "Arquivo",size,date))
                self.records[iid]=child
            self.render_details(None)
            suffix=" (mostrando até 500 itens)" if result.get("truncado") else ""
            self.notify(f"{len(self.records)} itens em {p}"+suffix)
        except Exception as exc: self.error(exc)

    def hsize(self,n):
        for unit in ("B","KB","MB","GB","TB"):
            if n<1024: return f"{n:.0f} {unit}" if unit=="B" else f"{n:.1f} {unit}"
            n=n/1024
        return f"{n:.1f} PB"

    def back(self):
        try:
            p=self.agent.safe(self.location.parent)
            self.show_folder(p)
        except PermissionError: self.show_folder(self.agent.desktop)

    def selected(self):
        ids=self.tree.selection()
        if not ids: return None
        return self.records.get(ids[0])

    def render_details(self,path):
        for widget in self.details.winfo_children(): widget.destroy()
        self.label(self.details,"DETALHES",12,bold=True,bg=PANEL).pack(anchor="w",padx=15,pady=(22,12))
        if path is None:
            self.label(self.details,"Selecione um arquivo ou pasta.",10,fg=MUTED,bg=PANEL,
                       wraplength=190,justify="left").pack(anchor="w",padx=15)
            return
        self.label(self.details,path.name,12,bold=True,bg=PANEL,wraplength=190,
                   justify="left").pack(anchor="w",padx=15,pady=(0,10))
        kind="Pasta" if path.is_dir() else "Arquivo"
        info=[("Tipo",kind),("Caminho",str(path))]
        try:
            stat=path.stat()
            if path.is_file(): info.append(("Tamanho",self.hsize(stat.st_size)))
            info.append(("Alterado",dt.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")))
        except OSError: pass
        for name,value in info:
            self.label(self.details,name,9,fg=MUTED,bg=PANEL).pack(anchor="w",padx=15,pady=(7,0))
            self.label(self.details,value,9,bg=PANEL,wraplength=195,
                       justify="left").pack(anchor="w",padx=15)

    def selected_details(self,_=None):
        self.render_details(self.selected())

    def open_selected(self):
        path=self.selected()
        if path is None: return self.notify("Selecione um item.")
        if path.is_dir(): return self.show_folder(path)
        try:
            # Clique manual no proprio PC nao concede acesso visual remoto ao MCP.
            if os.name=="nt":
                danger={".exe",".bat",".cmd",".ps1",".msi",".scr",
                        ".vbs",".js",".jse",".wsf",".reg",".lnk"}
                if path.suffix.lower() in danger:
                    if not messagebox.askyesno("Confirmar execução",
                        "Este arquivo pode executar comandos no seu computador.\n"
                        "Abrir mesmo assim?",parent=self.root):
                        return
                os.startfile(str(self.agent.safe(path)))
                self.notify("Solicitada abertura de "+path.name)
            else:
                result=self.agent.read_text(str(path))
                self.append(result["texto"][:10000])
        except Exception as exc: self.error(exc)

    def search(self):
        try:
            term=self.search_var.get().strip()
            if not term: return self.show_folder(self.location)
            r=self.agent.search_files(str(self.location),term,100)
            self.tree.delete(*self.tree.get_children())
            self.tree.heading("data",text="Pasta")
            self.records={}
            for full in r["resultados"]:
                p=Path(full)
                iid=self.tree.insert("",tk.END,text=p.name,
                                     values=("Pasta" if p.is_dir() else "Arquivo","—",str(p.parent)))
                self.records[iid]=p
            self.notify(f"{len(self.records)} resultados para '{term}'.")
        except Exception as exc:self.error(exc)


    def import_file(self):
        if not self.agent.write:return
        source=filedialog.askopenfilename(parent=self.root,title="Importar arquivo para a pasta atual")
        if not source:return
        try:
            import shutil
            original=Path(source)
            target=self.agent.safe(self.location/original.name)
            if target.exists():raise FileExistsError("Já existe um arquivo com esse nome")
            shutil.copy2(original,target)
            self.show_folder(self.location)
        except Exception as exc:self.error(exc)

    def export_file(self):
        selected=self.selected()
        if not selected:return self.notify("Selecione um arquivo.")
        if not selected.is_file():return self.notify("Escolha um arquivo, não uma pasta.")
        destination=filedialog.asksaveasfilename(parent=self.root,
                        initialfile=selected.name,title="Exportar cópia de arquivo")
        if not destination:return
        try:
            import shutil
            shutil.copy2(self.agent.safe(selected),destination)
            self.notify("Cópia exportada: "+Path(destination).name)
        except Exception as exc:self.error(exc)

    def new_folder(self):
        if not self.agent.write: return
        name=simpledialog.askstring("Nova pasta","Nome da nova pasta:",parent=self.root)
        if not name:return
        try:
            if name in (".","..") or Path(name).name!=name: raise ValueError("Nome inválido")
            dest=self.agent.safe(self.location/name)
            dest.mkdir(exist_ok=False)
            self.show_folder(self.location)
        except Exception as exc:self.error(exc)

    def rename_selected(self):
        if not self.agent.write:return
        old=self.selected()
        if not old:return self.notify("Selecione um item.")
        name=simpledialog.askstring("Renomear","Novo nome:",initialvalue=old.name,parent=self.root)
        if not name or name==old.name:return
        try:
            if name in (".","..") or Path(name).name!=name: raise ValueError("Nome inválido")
            new=self.agent.safe(old.parent/name)
            if new.exists(): raise FileExistsError("Já existe item com esse nome")
            old.rename(new)
            self.show_folder(self.location)
        except Exception as exc:self.error(exc)

    def delete_selected(self):
        if not self.agent.write:return
        p=self.selected()
        if not p:return self.notify("Selecione um item.")
        if p==self.location or p in self.agent.roots:return self.notify("Pasta protegida")
        if not messagebox.askyesno("Confirmar exclusão",
              f"Excluir permanentemente {p.name}?\nEsta operação não utiliza a Lixeira.",parent=self.root): return
        try:
            p=self.agent.safe(p)
            if p.is_symlink():p.unlink()
            elif p.is_dir():p.rmdir()  # somente pasta vazia
            else:p.unlink()
            self.show_folder(self.location)
        except Exception as exc:self.error(exc)

    def build_terminal(self):
        self.title("Terminal","PowerShell/CMD executados somente quando você autoriza.")
        wrap=tk.Frame(self.body,bg=PANEL)
        wrap.pack(fill="both",expand=True,padx=18,pady=12)
        self.terminal_output=tk.Text(wrap,bg="#080e14",fg=TEXT,font=("Consolas",11),
                  insertbackground=TEXT,relief="flat",wrap="word",state="disabled")
        self.terminal_output.pack(fill="both",expand=True,padx=10,pady=10)
        line=tk.Frame(wrap,bg=PANEL)
        line.pack(fill="x",padx=12,pady=(0,12))
        self.shell=tk.StringVar(value="powershell")
        selector=ttk.Combobox(line,textvariable=self.shell,values=("powershell","cmd"),
                              state="readonly",width=12)
        selector.pack(side="left",padx=(0,8))
        self.command=tk.Entry(line,bg=BTN,fg=TEXT,insertbackground=TEXT,
                              relief="flat",font=("Consolas",11))
        self.command.pack(side="left",fill="x",expand=True,ipady=9,padx=(0,8))
        self.command.bind("<Return>",lambda _:self.execute_command())
        self.button(line,"Executar",self.execute_command,primary=True,
                    enabled=self.agent.commands).pack(side="left")
        if not self.agent.commands:
            self.write_terminal("Terminal bloqueado por padrão. Configure NAVIX_ALLOW_COMMANDS=1 antes de iniciar o app.")
        else:self.write_terminal("Terminal autorizado. Comandos têm limite de 30 segundos.")

    def write_terminal(self,text):
        if self.mode!="Terminal":return
        self.terminal_output.configure(state="normal")
        self.terminal_output.insert("end",str(text)+"\n")
        self.terminal_output.see("end")
        self.terminal_output.configure(state="disabled")

    def execute_command(self):
        if not self.agent.commands:return
        command=self.command.get().strip()
        if not command:return
        self.command.delete(0,"end")
        self.write_terminal("> "+command)
        shell=self.shell.get()
        def worker():
            try:
                result=self.agent.run_command(command,shell=shell)
                out=(result["saida"] or "")+(result["erros"] or "")
                message=out or f"Concluído, código {result['codigo']}."
            except Exception as exc:message=str(exc)
            self.root.after(0,lambda:self.write_terminal(message))
        threading.Thread(target=worker,daemon=True).start()

    def build_processes(self):
        self.title("Processos","Consulta local de processos em execução. Não encerra processos automaticamente.")
        holder=tk.Frame(self.body,bg=BG)
        holder.pack(fill="both",expand=True,padx=18,pady=12)
        output=tk.Text(holder,bg=PANEL,fg=TEXT,font=("Consolas",10),
                       relief="flat",wrap="none")
        output.pack(fill="both",expand=True)
        def refresh():
            try:
                if os.name!="nt": raise RuntimeError("Disponível no Windows")
                r=subprocess.run(["tasklist","/fo","table"],capture_output=True,text=True,
                                 errors="replace",timeout=10,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                output.delete("1.0","end");output.insert("end",r.stdout or r.stderr)
            except Exception as exc:self.error(exc)
        self.button(holder,"Atualizar lista",refresh).pack(anchor="w",pady=9)
        refresh()

    def build_capture(self):
        self.title("Captura de Tela","Captura a tela principal quando o controle visual está habilitado.")
        self.label(self.body,"O controle visual está "+("AUTORIZADO." if self.agent.ui else "DESATIVADO por segurança."),
                   12,fg=GREEN if self.agent.ui else MUTED).pack(anchor="w",padx=20,pady=10)
        self.button(self.body,"Capturar tela",self.capture,primary=True,
                    enabled=self.agent.ui).pack(anchor="w",padx=20)
        self.label(self.body,"A captura é criada no computador. Não é enviada ao ChatGPT automaticamente.",
                   10,fg=MUTED).pack(anchor="w",padx=20,pady=14)

    def capture(self):
        try:
            result=self.agent.screenshot()
            import base64
            data=base64.b64decode(result["content"][0]["data"])
            from pathlib import Path
            import tempfile
            out=Path(tempfile.gettempdir())/("NavixCaptura_"+dt.datetime.now().strftime("%Y%m%d_%H%M%S")+".png")
            out.write_bytes(data)
            self.status.configure(text="Captura salva: "+str(out))
            messagebox.showinfo("Captura salva",str(out),parent=self.root)
        except Exception as exc:self.error(exc)

    def build_commands(self):
        self.title("Comandos","Recursos de controle local disponíveis na ponte MCP.")
        available=[("Listar pastas","Ativo"),("Buscar arquivos","Ativo"),
                   ("Ler textos","Ativo"),("Escrever textos","Ativo" if self.agent.write else "Bloqueado"),
                   ("PowerShell / CMD","Ativo" if self.agent.commands else "Bloqueado"),
                   ("Abrir sites / clicar / capturar","Ativo" if self.agent.ui else "Bloqueado")]
        for name,info in available:
            line=tk.Frame(self.body,bg=PANEL)
            line.pack(fill="x",padx=20,pady=4,ipady=9)
            self.label(line,name,11,bg=PANEL).pack(side="left",padx=15)
            self.label(line,info,10,fg=GREEN if info=="Ativo" else MUTED,bg=PANEL).pack(side="right",padx=18)

    def bridge_alive(self):
        return self.bridge is not None and self.bridge.poll() is None

    def check_bridge(self):
        if self.bridge_alive():
            self.connection.configure(text="●  Ponte MCP local ativa",fg=GREEN)
        else:
            self.connection.configure(text="●  Ponte local desligada",fg=MUTED)
        self.root.after(1200,self.check_bridge)

    def start_bridge(self):
        if self.bridge_alive():return self.status.configure(text="Ponte local já iniciada.")
        try:
            if getattr(sys,"frozen",False):
                executable=Path(sys.executable).with_name("NavixBridge.exe")
                if not executable.is_file():raise FileNotFoundError(str(executable))
                argv=[str(executable)]
            else:
                script=Path(__file__).with_name("navix_remote.py")
                argv=[sys.executable,str(script)]
            self.bridge=subprocess.Popen(argv,cwd=str(Path(argv[-1]).parent),
                    creationflags=getattr(subprocess,"CREATE_NEW_CONSOLE",0))
            self.status.configure(text="Ponte local iniciada em 127.0.0.1:8765")
            messagebox.showinfo("Ponte MCP local",
                "A ponte só atende seu computador (127.0.0.1).\n"
                "Ela NÃO conecta automaticamente esta conversa do ChatGPT.\n"
                "Não compartilhe o token nem abra portas no roteador.",parent=self.root)
        except Exception as exc:self.error(exc)

    def stop_bridge(self):
        if self.bridge_alive():
            self.bridge.terminate()
            try:self.bridge.wait(timeout=2)
            except subprocess.TimeoutExpired:self.bridge.kill()
            self.bridge=None
            self.status.configure(text="Ponte local encerrada.")
        else:self.status.configure(text="Nenhuma ponte iniciada pelo painel.")

    def build_settings(self):
        self.title("Configurações","Permissões locais e conexão MCP.")
        self.label(self.body,"A ponte remota não conecta o ChatGPT automaticamente.",
                12,bold=True).pack(anchor="w",padx=20,pady=(12,4))
        self.label(self.body,"Servidor: 127.0.0.1:8765 (somente no computador)",
                   10,fg=MUTED).pack(anchor="w",padx=20,pady=7)
        line=tk.Frame(self.body,bg=BG)
        line.pack(anchor="w",padx=20,pady=14)
        self.button(line,"Iniciar ponte MCP local",self.start_bridge,primary=True).pack(side="left",padx=(0,9))
        self.button(line,"Parar ponte",self.stop_bridge).pack(side="left")
        for flag,enabled in (("Escrita",self.agent.write),("Terminal",self.agent.commands),("Mouse e captura",self.agent.ui)):
            self.label(self.body,f"{flag}: {'autorizado' if enabled else 'bloqueado por padrão'}",
                    11,fg=GREEN if enabled else MUTED).pack(anchor="w",padx=20,pady=5)
        self.label(self.body,"Ativações opcionais exigem reiniciar o aplicativo com as variáveis NAVIX_ALLOW_*.\n"
                   "Nunca execute como Administrador sem necessidade.",10,fg=MUTED,
                   justify="left").pack(anchor="w",padx=20,pady=12)

    def build_about(self):
        self.title("Sobre","Navix Livre • programa independente, código aberto (MIT).")
        msg=("Painel Windows criado com Tkinter.\n\n"
             "Recursos: navegador de arquivos autorizado, busca, leitura de textos, "
             "terminal opcional, captura opcional, processos e ponte MCP local.\n\n"
             "Não é o Desktop Commander original. Não possui integração externa automática "
             "com o ChatGPT, OAuth completo nem controle de navegador próprio.\n\n"
             "Sem mensalidade do programa. Serviços externos podem cobrar.\n"
             "A versão ainda deve ser validada no seu computador real.")
        self.label(self.body,msg,12,fg=MUTED,justify="left",wraplength=690).pack(anchor="w",padx=20,pady=15)

    def close(self):
        if self.bridge_alive():
            if not messagebox.askyesno("Fechar Navix Livre",
                 "A ponte MCP está ativa. Fechar aplicativo e encerrar a ponte?",parent=self.root):return
            self.stop_bridge()
        self.root.destroy()

    def run(self):self.root.mainloop()

def run_gui(agent):
    NavixWindow(agent).run()

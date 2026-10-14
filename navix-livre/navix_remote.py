#!/usr/bin/env python3
"""Bridge MCP HTTP local, autenticado, sem assinatura. Nao expor sem HTTPS."""
import argparse
import base64
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
from navix_livre import Agent, VERSION, call, tools

TOKEN_FILE=Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "NavixLivre" / "bridge.token"
MAX_BODY=128*1024

def load_token(path=TOKEN_FILE):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        token=path.read_text(encoding="utf-8").strip()
        if len(token)<50: raise ValueError("Token invalido: servidor nao iniciado")
        return token
    else:
        token=secrets.token_urlsafe(48)
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            f.write(token+"\n")
        return token

def make_handler(agent,token):
    class Handler(BaseHTTPRequestHandler):
        server_version="NavixLivre/0.2"
        sys_version=""
        def log_message(self,*_args):
            pass
        def respond(self,code,value=None,extra=None):
            data=b"" if value is None else json.dumps(value,ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(data)))
            for k,v in (extra or {}).items(): self.send_header(k,v)
            self.end_headers()
            if data: self.wfile.write(data)
        def authorized(self):
            auth=self.headers.get("Authorization","")
            supplied=auth[7:] if auth.startswith("Bearer ") else ""
            if not hmac.compare_digest(supplied,token):
                self.respond(401,{"error":"Acesso negado"},{"WWW-Authenticate":'Bearer realm="Navix Livre"'})
                return False
            if self.headers.get("Origin"):
                self.respond(403,{"error":"Origem de navegador nao permitida"})
                return False
            return True
        def do_GET(self):
            if self.path!="/health":
                self.respond(404,{"error":"Rota inexistente"})
                return
            if not self.authorized(): return
            self.respond(200,{"status":"online","version":VERSION})
        def allowed_tools(self):
            allowed={"status","list_directory","search_files","read_text"}
            if agent.write: allowed.add("write_text")
            if agent.commands: allowed.add("run_command")
            if agent.ui: allowed.update({"open_url","open_path","click","screenshot"})
            return allowed
        def do_POST(self):
            if self.path!="/mcp":
                self.respond(404,{"error":"Rota inexistente"})
                return
            if not self.authorized(): return
            if self.headers.get("Content-Type","").split(";")[0].lower()!="application/json":
                self.respond(415,{"error":"Content-Type invalido"})
                return
            try: size=int(self.headers.get("Content-Length","-1"))
            except ValueError: size=-1
            if not 0<size<=MAX_BODY:
                self.respond(413,{"error":"Corpo ausente ou grande demais"})
                return
            try:
                msg=json.loads(self.rfile.read(size))
                if not isinstance(msg,dict) or msg.get("jsonrpc")!="2.0":
                    raise ValueError("Esperado JSON-RPC 2.0")
                if "id" not in msg:
                    self.respond(202)
                    return
                method=msg.get("method")
                if method=="initialize":
                    proto=(msg.get("params") or {}).get("protocolVersion","2025-03-26")
                    if proto not in ("2024-11-05","2025-03-26","2025-06-18"): proto="2025-03-26"
                    result={"protocolVersion":proto,"capabilities":{"tools":{}},
                            "serverInfo":{"name":"navix-livre","version":VERSION}}
                elif method=="ping": result={}
                elif method=="tools/list":
                    result={"tools":[t for t in tools() if t["name"] in self.allowed_tools()]}
                elif method=="tools/call":
                    p=msg.get("params") or {}
                    name=p.get("name")
                    if name not in self.allowed_tools():
                        result={"content":[{"type":"text","text":"Ferramenta nao autorizada"}],"isError":True}
                    else:
                        try:
                            args=p.get("arguments") or {}
                            if not isinstance(args,dict): raise ValueError("Argumentos invalidos")
                            result=call(agent,name,args)
                        except Exception as e:
                            result={"content":[{"type":"text","text":type(e).__name__+": "+str(e)}],
                                    "isError":True}
                else:
                    self.respond(200,{"jsonrpc":"2.0","id":msg["id"],
                                      "error":{"code":-32601,"message":"Metodo desconhecido"}})
                    return
                self.respond(200,{"jsonrpc":"2.0","id":msg["id"],"result":result})
            except (ValueError,TypeError) as e:
                self.respond(400,{"error":str(e)})
            except Exception:
                self.respond(500,{"error":"Falha interna"})
    return Handler

def main():
    parser=argparse.ArgumentParser(description="Ponte MCP local com token de acesso")
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--show-token-path",action="store_true")
    cfg=parser.parse_args()
    if cfg.show_token_path:
        print(str(TOKEN_FILE))
        return
    if not 1024<=cfg.port<=65535:
        parser.error("Porta fora do intervalo permitido")
    token=load_token()
    server=HTTPServer(("127.0.0.1",cfg.port),make_handler(Agent(),token))
    print("Navix Livre MCP: http://127.0.0.1:%d/mcp" % cfg.port,flush=True)
    print("Token criado no seu computador. Nao compartilhe com outras pessoas.",flush=True)
    print("Acesso externo requer tunel HTTPS e cliente MCP autorizado.",flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=="__main__": main()

"""AEGIS mobile web control, read-only and loopback-only by default.

Mobile access requires a separately authenticated HTTPS tunnel/VPN.
"""
from __future__ import annotations
import html,hmac,json,secrets
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit
from aegis_core.engine import diagnostic,Audit,Workspace
from aegis_core.guardian import Guardian

HTML="""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AEGIS Mobile</title><style>
:root{color-scheme:dark}body{font:16px system-ui;background:#101827;color:#e4ebfa;max-width:650px;margin:auto;padding:20px}
section{background:#1e293b;padding:16px;border-radius:14px;margin-top:16px}
button,input{padding:13px;border-radius:9px;font:inherit;max-width:100%;box-sizing:border-box}
button{background:#3b82f6;border:0;color:white;margin:6px}
pre{white-space:pre-wrap;word-break:break-word;font-size:13px}
</style></head><body><h1>AEGIS Mobile</h1><p>Monitoramento remoto supervisionado. Somente leitura.</p>
<section><label for="token">Token de sessão:</label><input id="token" type="password" autocomplete="off" placeholder="Token fornecido no PC">
<button onclick="check()">Conectar</button></section><section><button onclick="query('/v1/diagnostics')">Diagnóstico</button><button onclick="query('/v1/guardian')">Guardião</button>
<button onclick="query('/v1/files')">Arquivos</button><pre id="out">Aguardando autenticação...</pre></section>
<script>
const out=document.getElementById('out');
async function query(path){
try{const r=await fetch(path,{headers:{Authorization:'Bearer '+document.getElementById('token').value},cache:'no-store'});
const v=await r.json();out.textContent=JSON.stringify(v,null,2);}
catch(e){out.textContent='Falha de comunicação: '+e.message;}}
function check(){query('/v1/health')}
</script></body></html>"""

class MobileServer(ThreadingHTTPServer):
 daemon_threads=True
 def __init__(self, address, token, workspace, audit):
  if address[0] not in ("127.0.0.1","::1"):raise ValueError("Loopback only; use a secure VPN + authenticated HTTPS reverse proxy")
  if len(token)<32:raise ValueError("Token too short")
  self.token=token
  self.workspace=Workspace(workspace)
  self.guardian=Guardian(workspace,audit)
  self.audit=audit
  super().__init__(address,MobileHandler)
  self.guardian.start()
 def server_close(self):
  self.guardian.stop()
  super().server_close()

class MobileHandler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def respond(self,status,payload,typ="application/json; charset=utf-8"):
  raw=(payload.encode("utf-8") if isinstance(payload,str) else json.dumps(payload,ensure_ascii=False).encode("utf-8"))
  self.send_response(status)
  self.send_header("Content-Type",typ)
  self.send_header("Cache-Control","no-store")
  self.send_header("X-Content-Type-Options","nosniff")
  self.send_header("Content-Security-Policy","default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'")
  self.send_header("Content-Length",str(len(raw)))
  self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=="/":return self.respond(200,HTML,"text/html; charset=utf-8")
  if not hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+self.server.token):
   self.server.audit.add("mobile.login","denied",{"source":self.client_address[0]})
   return self.respond(401,{"error":"unauthorized"})
  if path=="/v1/health":return self.respond(200,{"online":True,"mode":"read-only"})
  if path=="/v1/diagnostics":return self.respond(200,diagnostic())
  if path=="/v1/guardian":return self.respond(200,self.server.guardian.status())
  if path=="/v1/files":return self.respond(200,{"files":self.server.workspace.inventory(maximum=100)})
  return self.respond(404,{"error":"not found"})
 def do_POST(self):self.respond(405,{"error":"read-only"})

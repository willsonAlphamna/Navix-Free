"""AEGIS remotely reachable agent behind an authenticated overlay or TLS reverse proxy.
Default bind is localhost; does not expose arbitrary shell or secret files.
"""
from __future__ import annotations
import hmac,json,pathlib,os,secrets,threading,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit
from .engine import Audit,diagnostic,Workspace
from .guardian import Guardian
MAX_BODY=4096
class RateLimiter:
 def __init__(self):self.events={};self.lock=threading.Lock()
 def allowed(self,identifier):
  now=time.monotonic()
  with self.lock:
   past=[t for t in self.events.get(identifier,[]) if now-t<60]
   if len(past)>=30:return False
   past.append(now);self.events[identifier]=past
   return True
class RemoteAgent(ThreadingHTTPServer):
 allow_reuse_address=True
 daemon_threads=True
 def __init__(self, address, token, root, audit, *, allow_external=False):
  host,port=address
  if not allow_external and host not in ("127.0.0.1","::1"):
   raise ValueError("Only loopback permitted without an external TLS/overlay configuration")
  if len(token)<32:raise ValueError("Token must have at least 32 characters")
  self.token=token
  self.audit=audit
  self.workspace=Workspace(root)
  self.guardian=Guardian(root,audit)
  self.limiter=RateLimiter()
  super().__init__(address,AgentHandler)
  self.guardian.start()
 def server_close(self):
  self.guardian.stop()
  super().server_close()
class AgentHandler(BaseHTTPRequestHandler):
 def log_message(self,*_):pass
 def respond(self,status,content):
  raw=json.dumps(content,ensure_ascii=False).encode()
  self.send_response(status)
  self.send_header("Content-Type","application/json; charset=utf-8")
  self.send_header("Cache-Control","no-store")
  self.send_header("X-Content-Type-Options","nosniff")
  self.send_header("Content-Length",str(len(raw)))
  self.end_headers()
  self.wfile.write(raw)
 def do_GET(self):
  if not self.server.limiter.allowed(self.client_address[0]):
   return self.respond(429,{"error":"rate_limit"})
  supplied=self.headers.get("Authorization","")
  if not hmac.compare_digest(supplied,"Bearer "+self.server.token):
   self.server.audit.add("remote.auth","denied",{"client":self.client_address[0]})
   return self.respond(401,{"error":"unauthorized"})
  path=urlsplit(self.path).path
  if path=="/v1/health":return self.respond(200,{"online":True,"version":"0.1","access":"read-only"})
  if path=="/v1/diagnostics":return self.respond(200,diagnostic())
  if path=="/v1/guardian":return self.respond(200,self.server.guardian.status())
  if path=="/v1/files":return self.respond(200,{"files":self.server.workspace.inventory(maximum=200)})
  return self.respond(404,{"error":"not_found"})
 def do_POST(self):return self.respond(405,{"error":"read_only"})

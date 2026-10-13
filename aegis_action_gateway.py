"""AEGIS mobile action gateway: localhost only, one-time on-PC operator approval.
Access outside PC requires separately configured private VPN/HTTPS.
"""
import json,hmac,secrets,threading,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from aegis_core.desktop_control import DesktopControl
from aegis_core.engine import Audit
class Gateway(ThreadingHTTPServer):
 daemon_threads=True
 def __init__(self,address,token,audit,desktop=None):
  if address[0] not in ("127.0.0.1","::1"):raise ValueError("loopback only")
  if len(token)<32:raise ValueError("weak token")
  self.token=token;self.audit=audit
  self.desktop=desktop or DesktopControl()
  self.approved_until=0
  self.lock=threading.Lock()
  super().__init__(address,Handler)
 def allow_session(self,seconds=300):
  if not 0<seconds<=900:raise ValueError("invalid duration")
  with self.lock:self.approved_until=time.monotonic()+seconds
 def revoke(self):
  with self.lock:self.approved_until=0
 def is_approved(self):
  with self.lock:return time.monotonic()<self.approved_until
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def respond(self,status,body):
  raw=json.dumps(body).encode()
  self.send_response(status)
  self.send_header("Content-Type","application/json")
  self.send_header("Cache-Control","no-store")
  self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  if not hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+self.server.token):
   return self.respond(401,{"error":"unauthorized"})
  if not self.server.is_approved():return self.respond(403,{"error":"local approval required"})
  size=int(self.headers.get("Content-Length","0"))
  if size<=0 or size>2048:return self.respond(413,{"error":"invalid request size"})
  try:
   action=json.loads(self.rfile.read(size))
   op=action.get("op")
   with self.server.lock:
    if op=="move":self.server.desktop.move(action["x"],action["y"])
    elif op=="click":self.server.desktop.click(action["x"],action["y"])
    elif op=="scroll":self.server.desktop.scroll(action["steps"])
    elif op=="text":self.server.desktop.type_text(action["value"])
    else:return self.respond(400,{"error":"invalid action"})
   self.server.audit.add("mobile.action","completed",{"operation":op})
   return self.respond(200,{"ok":True})
  except (ValueError,TypeError,KeyError,OverflowError) as exc:
   return self.respond(400,{"error":type(exc).__name__})
  except OSError as exc:
   return self.respond(503,{"error":"desktop unavailable"})

"""AEGIS local control endpoint: loopback only, authenticated, read-only.
Not a public remote access server. Requires a separately designed secure transport.
"""
from __future__ import annotations
import hmac, json, os, secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from aegis_core.engine import diagnostic
from aegis_core.guardian import Guardian
from aegis_core.engine import Audit
from pathlib import Path

class ControlServer(ThreadingHTTPServer):
    def __init__(self, address, token, workspace, audit):
        host,port=address
        if host not in ("127.0.0.1","::1"):raise ValueError("Only loopback connections supported")
        if len(token)<32:raise ValueError("Strong token required")
        self.token=token
        self.guardian=Guardian(workspace,audit)
        super().__init__(address,Handler)
    def server_close(self):
        self.guardian.stop()
        super().server_close()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):pass
    def do_GET(self):
        provided=self.headers.get("Authorization","")
        required="Bearer "+self.server.token
        if not hmac.compare_digest(provided,required):
            return self.respond(401,{"error":"unauthorized"})
        if self.path=="/health":
            return self.respond(200,{"status":"ok"})
        if self.path=="/diagnostic":
            return self.respond(200,diagnostic())
        if self.path=="/guardian":
            return self.respond(200,self.server.guardian.status())
        return self.respond(404,{"error":"not found"})
    def respond(self,status,payload):
        raw=json.dumps(payload,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--workspace",default=".")
    p.add_argument("--port",type=int,default=8765)
    p.add_argument("--audit",default=".aegis/local-control.jsonl")
    args=p.parse_args()
    token=os.environ.get("AEGIS_LOCAL_TOKEN","")
    if len(token)<32:
        raise SystemExit("Set AEGIS_LOCAL_TOKEN to a random 32+ character secret in your environment.")
    server=ControlServer(("127.0.0.1",args.port),token,args.workspace,Audit(args.audit))
    print("AEGIS local endpoint bound to 127.0.0.1",flush=True)
    try:server.serve_forever()
    finally:server.server_close()
if __name__=="__main__":main()

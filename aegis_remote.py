"""Start the AEGIS read-only control agent on loopback, with a persisted local token.

Do not forward this port over the public internet. Use an authenticated overlay and
only enable exposure after HTTPS and access-control tests.
"""
import argparse,os,pathlib,secrets
from aegis_core.remote_agent import RemoteAgent
from aegis_core.engine import Audit
def main(argv=None):
 p=argparse.ArgumentParser()
 p.add_argument("--workspace",default=".")
 p.add_argument("--port",type=int,default=8766)
 p.add_argument("--audit",default=".aegis/remote.jsonl")
 args=p.parse_args(argv)
 token=os.environ.get("AEGIS_REMOTE_TOKEN")
 if not token:raise SystemExit("AEGIS_REMOTE_TOKEN not set; configure a private token before launch.")
 server=RemoteAgent(("127.0.0.1",args.port),token,args.workspace,Audit(args.audit))
 print("AEGIS remote agent listening on loopback port",args.port,flush=True)
 try:server.serve_forever()
 finally:server.server_close()
if __name__=="__main__":main()

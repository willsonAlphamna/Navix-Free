"""Local guardian supervisor. No unattended destructive actions."""
import argparse,json,pathlib,signal,threading,time
from aegis_core.engine import Audit
from aegis_core.guardian import Guardian
from aegis_core.advisor import Advisor

def main(argv=None):
 p=argparse.ArgumentParser()
 p.add_argument("--workspace",default=".")
 p.add_argument("--audit",default=".aegis/guardian.jsonl")
 p.add_argument("--interval",type=float,default=10)
 p.add_argument("--once",action="store_true")
 args=p.parse_args(argv)
 if args.interval<1:p.error("interval must be at least 1 second")
 audit=Audit(args.audit)
 guardian=Guardian(args.workspace,audit,interval=args.interval)
 advisor=Advisor()
 if args.once:
  guardian.check_once()
  print(json.dumps({"guardian":guardian.status(),"advice":advisor.assess(guardian.last_findings).__dict__},ensure_ascii=False))
  return 0
 stop=threading.Event()
 def handle_signal(*_):stop.set()
 signal.signal(signal.SIGINT,handle_signal)
 if hasattr(signal,"SIGTERM"):signal.signal(signal.SIGTERM,handle_signal)
 guardian.start()
 print("AEGIS Guardian active; Ctrl+C to stop",flush=True)
 try:
  while not stop.wait(1):
   pass
 finally:
  guardian.stop()
  print("AEGIS Guardian stopped",flush=True)
 return 0
if __name__=="__main__":raise SystemExit(main())

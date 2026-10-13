"""AEGIS CLI: supervised local diagnostics and workspace operations."""
import argparse, json, pathlib
from aegis_core.engine import Workspace, Audit, diagnostic, run_diagnostic
def main(argv=None):
    p=argparse.ArgumentParser(description="AEGIS workstation diagnostics (local)")
    p.add_argument("--workspace",default=".")
    p.add_argument("--audit",default=".aegis/audit.jsonl")
    sub=p.add_subparsers(dest="operation",required=True)
    sub.add_parser("system")
    sub.add_parser("inventory")
    h=sub.add_parser("sha256");h.add_argument("file")
    cmd=sub.add_parser("diagnostic");cmd.add_argument("name",choices=["hostname","ip","processes","network"])
    args=p.parse_args(argv)
    audit=Audit(args.audit)
    try:
        if args.operation=="system":result=diagnostic()
        elif args.operation=="inventory":result=Workspace(args.workspace).inventory()
        elif args.operation=="sha256":result={"sha256":Workspace(args.workspace).hash_file(args.file)}
        else:result=run_diagnostic(args.name,audit)
        audit.add("cli."+args.operation,"completed")
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except Exception as e:
        audit.add("cli."+args.operation,"failed",{"error":str(e)})
        print(json.dumps({"error":str(e)},ensure_ascii=False))
        return 1
if __name__=="__main__":raise SystemExit(main())

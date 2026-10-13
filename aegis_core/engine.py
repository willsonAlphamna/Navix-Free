"""Supervised local orchestration, Windows diagnostics and auditable operations."""
from __future__ import annotations
import concurrent.futures, hashlib, json, os, pathlib, platform, shutil, subprocess, threading, time, uuid
from datetime import datetime, timezone

SAFE_COMMANDS = {
    "hostname": ["hostname"],
    "ip": ["ipconfig", "/all"] if os.name == "nt" else ["hostname"],
    "processes": ["tasklist", "/fo", "csv"] if os.name == "nt" else ["ps", "-ef"],
    "network": ["netstat", "-ano"] if os.name == "nt" else ["netstat", "-an"],
}
MAX_SCAN = 5000
MAX_HASH_SIZE = 100 * 1024 * 1024

class Audit:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
    def add(self, event, status, details=None):
        record = {"at": datetime.now(timezone.utc).isoformat(), "event": event,
                  "status": status, "details": details or {}}
        with self.lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

class Workspace:
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve(strict=True)
        if not self.root.is_dir(): raise ValueError("Workspace must be a directory")
    def resolve(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root): raise PermissionError("Outside workspace")
        return path
    def inventory(self, maximum=MAX_SCAN):
        out = []
        for base, dirs, names in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__"}]
            for name in names:
                path = pathlib.Path(base) / name
                if path.is_symlink(): continue
                try:
                    stat = path.stat()
                    out.append({"path":str(path.relative_to(self.root)),
                                "size":stat.st_size, "mtime_ns":stat.st_mtime_ns})
                except OSError: continue
                if len(out) >= maximum:return out
        return out
    def hash_file(self, relative):
        path = self.resolve(relative)
        if not path.is_file() or path.stat().st_size > MAX_HASH_SIZE:
            raise ValueError("File missing or too large")
        digest = hashlib.sha256()
        with path.open("rb") as inp:
            for chunk in iter(lambda: inp.read(1024*1024), b""): digest.update(chunk)
        return digest.hexdigest()
    def copy_safe(self, source, destination):
        src, dst = self.resolve(source), self.resolve(destination)
        if not src.is_file(): raise ValueError("Source missing")
        if src == dst: raise ValueError("Source equals destination")
        with src.open("rb") as inp, dst.open("xb") as out:
            shutil.copyfileobj(inp, out, 1024*1024)
        return str(dst)

class Engine:
    def __init__(self, workspace, audit, max_workers=3):
        if not 1 <= max_workers <= 4: raise ValueError("Worker limit 1..4")
        self.workspace = workspace
        self.audit = audit
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.jobs = {}
        self.lock = threading.Lock()
    def submit(self, label, callback, *args):
        job_id = uuid.uuid4().hex
        with self.lock:self.jobs[job_id] = {"label":label,"state":"queued","created":time.time()}
        def run():
            with self.lock:self.jobs[job_id]["state"] = "running"
            try:
                result = callback(*args)
                with self.lock:self.jobs[job_id].update(state="completed",result=result)
                self.audit.add(label, "completed", {"job_id":job_id})
            except Exception as error:
                with self.lock:self.jobs[job_id].update(state="failed",error=str(error))
                self.audit.add(label, "failed", {"job_id":job_id,"error":str(error)})
                raise
        future = self.pool.submit(run)
        return job_id, future
    def status(self, job_id):
        with self.lock:return dict(self.jobs[job_id])
    def shutdown(self):self.pool.shutdown(wait=True, cancel_futures=True)

def diagnostic():
    disk = shutil.disk_usage(pathlib.Path.home())
    return {"hostname":platform.node(),"platform":platform.platform(),
            "cpu_logical":os.cpu_count(),"disk_free_bytes":disk.free}

def run_diagnostic(command, audit, timeout=15):
    if command not in SAFE_COMMANDS:raise PermissionError("Unknown diagnostic")
    try:
        result = subprocess.run(SAFE_COMMANDS[command], shell=False, capture_output=True,
                                text=True, errors="replace", timeout=timeout)
        audit.add("diagnostic", "completed", {"command":command,"code":result.returncode})
        return {"code":result.returncode,"stdout":result.stdout[:200000],
                "stderr":result.stderr[:20000]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        audit.add("diagnostic","failed",{"command":command,"error":str(exc)})
        raise

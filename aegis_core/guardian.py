"""AEGIS Guardian: local, deterministic risk evaluation and continuous supervision.

Never executes an action itself. Decisions must be explicitly approved by a human.
No external connection, credentials, elevation, or background persistence.
"""
from __future__ import annotations
import dataclasses, fnmatch, hashlib, json, os, pathlib, threading, time
from datetime import datetime, timezone

@dataclasses.dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    reason: str
    subject: str

class Guardian:
    HIGH_RISK = frozenset({"delete", "terminate", "shell", "install", "registry", "network-expose", "write", "browser-submit"})
    def __init__(self, root, audit, interval=10, max_files=5000):
        self.root = pathlib.Path(root).resolve(strict=True)
        if not self.root.is_dir(): raise ValueError("root must be a directory")
        if interval < 1: raise ValueError("interval must be >= 1")
        if not 1 <= max_files <= 10000: raise ValueError("invalid file limit")
        self.audit=audit
        self.interval=interval
        self.max_files=max_files
        self._baseline=None
        self._stop=threading.Event()
        self._thread=None
        self._lock=threading.RLock()
        self.last_findings=[]
    def evaluate_action(self, action, subject, approved=False):
        action=str(action).casefold()
        if action in self.HIGH_RISK and not approved:
            finding=Finding("high","approval_required","Human approval required",str(subject))
            self.audit.add("guardian.block","blocked",dataclasses.asdict(finding))
            return False, finding
        if action not in self.HIGH_RISK and action not in {"read","list","hash","diagnostic","navigate"}:
            finding=Finding("high","unknown_action","Action not registered",str(subject))
            self.audit.add("guardian.block","blocked",dataclasses.asdict(finding))
            return False,finding
        self.audit.add("guardian.allow","ok",{"action":action,"subject":str(subject)})
        return True,None
    def snapshot(self):
        result={}
        count=0
        for base,dirs,files in os.walk(self.root):
            dirs[:]=[d for d in dirs if d.casefold() not in {".git","node_modules","__pycache__"} and not pathlib.Path(base,d).is_symlink()]
            for name in files:
                path=pathlib.Path(base,name)
                if path.is_symlink():continue
                try:
                    st=path.stat()
                    relative=str(path.relative_to(self.root))
                    result[relative]=(st.st_size,st.st_mtime_ns)
                except OSError:continue
                count+=1
                if count>=self.max_files:return result
        return result
    def check_once(self):
        latest=self.snapshot()
        with self._lock:
            previous=self._baseline
            self._baseline=latest
        if previous is None:
            self.audit.add("guardian.baseline","ok",{"files":len(latest)})
            return []
        findings=[]
        for name in latest.keys()-previous.keys():
            findings.append(Finding("info","added","File appeared",name))
        for name in previous.keys()-latest.keys():
            findings.append(Finding("medium","removed","File disappeared",name))
        for name in latest.keys()&previous.keys():
            if latest[name]!=previous[name]:
                findings.append(Finding("medium","changed","File metadata changed",name))
        with self._lock:self.last_findings=findings[:500]
        if findings:
            self.audit.add("guardian.change","attention",{"count":len(findings),"sample":[dataclasses.asdict(f) for f in findings[:20]]})
        return findings
    def _loop(self):
        while not self._stop.is_set():
            try:self.check_once()
            except Exception as exc:self.audit.add("guardian.error","failed",{"error":str(exc)[:200]})
            self._stop.wait(self.interval)
    def start(self):
        if self._thread and self._thread.is_alive():return False
        self._stop.clear()
        self._thread=threading.Thread(target=self._loop,daemon=True,name="aegis-guardian")
        self._thread.start()
        return True
    def stop(self):
        self._stop.set()
        if self._thread:self._thread.join(timeout=3)
    def status(self):
        with self._lock:
            return {"running":bool(self._thread and self._thread.is_alive()),"observed_files":len(self._baseline or {}),"last_findings":[dataclasses.asdict(f) for f in self.last_findings]}

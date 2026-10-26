"""Session permissions and privacy-preserving audit trail."""
import json
import secrets
import threading
import time
from pathlib import Path


class Session:
    def __init__(self, directory: Path, clock=time.monotonic):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.lock = threading.RLock()
        self.token = secrets.token_urlsafe(32)
        self.until = 0.0
        self.unlimited = False
        self.permissions = set()

    def activate(self, permissions, minutes=30):
        if minutes is not None and (isinstance(minutes, bool) or not isinstance(minutes, int)
                                    or not 1 <= minutes <= 240):
            raise ValueError('A sessão deve durar de 1 a 240 minutos, ou Sem prazo.')
        if not set(permissions) <= {'browser', 'desktop', 'files', 'commands'}:
            raise ValueError('Permissão desconhecida.')
        with self.lock:
            self.permissions = set(permissions)
            self.unlimited = minutes is None
            self.until = 0 if self.unlimited else self.clock() + minutes * 60
        self.audit('session_start', 'ok')

    def stop(self):
        with self.lock:
            self.until = 0
            self.unlimited = False
            self.permissions.clear()
            self.token = secrets.token_urlsafe(32)
        self.audit('session_stop', 'ok')

    def authenticates(self, token):
        with self.lock:
            return isinstance(token, str) and bool(token) and token.isascii() and secrets.compare_digest(token, self.token)

    def require(self, permission):
        with self.lock:
            if (not self.unlimited and self.clock() >= self.until) or permission not in self.permissions:
                self.audit(permission, 'denied')
                raise PermissionError('Sessão encerrada ou permissão desativada no painel.')

    def status(self):
        with self.lock:
            seconds = None if self.unlimited else max(0, int(self.until - self.clock()))
            active = self.unlimited or seconds > 0
            status = {'active': active, 'remaining_seconds': seconds,
                      'permissions': sorted(self.permissions) if active else []}
            if self.unlimited:
                status['unlimited'] = True
            return status

    def audit(self, action, result):
        # Never record tokens, typed text, URLs, page content or screenshots.
        with self.lock:
            path = self.directory / 'audit.jsonl'
            if path.exists() and path.stat().st_size > 2_000_000:
                path.replace(self.directory / 'audit.previous.jsonl')
            with path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'time': time.time(), 'action': action,
                                         'result': result}) + '\n')

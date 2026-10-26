"""Structured, redacted Navix diagnostics and bounded event rotation."""
from datetime import datetime, timezone
import json
from pathlib import Path
import threading


class Diagnostics:
    MAX_BYTES = 1_500_000
    LEVELS = {'info', 'warning', 'error'}

    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'diagnostics.jsonl'
        self.lock = threading.Lock()

    def record(self, component, action, result='ok', level='info', code=''):
        # Intentionally excludes arbitrary exceptions, command arguments,
        # text typed by the user, screenshots, URLs, passwords and token values.
        row = {
            'time_utc': datetime.now(timezone.utc).isoformat(),
            'component': str(component)[:48],
            'action': str(action)[:64],
            'result': str(result)[:24],
            'level': level if level in self.LEVELS else 'warning',
            'code': str(code)[:48],
        }
        with self.lock:
            if self.path.exists() and self.path.stat().st_size > self.MAX_BYTES:
                self.path.replace(self.directory / 'diagnostics.previous.jsonl')
            with self.path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')

    def report(self, session, service, tunnel, browser=None):
        state = session.status()
        process = tunnel.process
        recent = []
        try:
            with self.lock, self.path.open(encoding='utf-8') as stream:
                recent = list(stream)[-100:]
        except OSError:
            pass
        return {
            'report_version': 1,
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'server_ready': bool(service.ready),
            'server_port': service.port,
            'session_active': state['active'],
            'session_unlimited': state.get('unlimited', False),
            'permissions': state['permissions'],
            'tunnel_state': tunnel.check(),
            'tunnel_process_alive': bool(process and process.poll() is None),
            'tunnel_local_health': getattr(tunnel, 'health_state', 'unknown'),
            'tunnel_retry_count': getattr(tunnel, 'attempts', 0),
            'tunnel_last_error_category': (
                'requires_attention' if 'Diagnóstico falhou' in getattr(tunnel, 'error', '') else
                'runtime_unavailable' if getattr(tunnel, 'error', '') else 'none'
            ),
            'browser_worker_present': bool(browser is not None),
            'events': [json.loads(line) for line in recent if line.strip()],
            'secrets_included': False,
        }

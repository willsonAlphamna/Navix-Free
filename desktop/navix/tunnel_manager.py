"""Owner-controlled Secure MCP Tunnel lifecycle.

No key or local Bearer token is sent to a shell command line, saved to a log,
or shipped in the installer. A user must authorize a Navix session first.
"""

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time


TUNNEL_ID = re.compile(r'^tunnel_[a-fA-F0-9]{32}$')
_BACKOFF = (3, 8, 20, 45, 90)


def bundled_tunnel_client():
    """Find the signed-upstream binary included in the Windows installer."""
    locations = [Path(sys.executable).resolve().parent / 'tunnel-client.exe']
    if getattr(sys, '_MEIPASS', None):
        locations.insert(0, Path(sys._MEIPASS) / 'tunnel-client.exe')
    locations.append(Path(__file__).resolve().parent.parent / 'tunnel-client.exe')
    for location in locations:
        if location.is_file():
            return str(location)
    return shutil.which('tunnel-client')


class _Blob(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(data, protect):
    """Bind an opt-in saved secret to the current Windows login via DPAPI."""
    if sys.platform != 'win32':
        raise OSError('Armazenamento protegido disponível somente no Windows.')
    raw = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = _Blob(len(data), ctypes.cast(raw, ctypes.POINTER(ctypes.c_ubyte)))
    result = _Blob()
    library = ctypes.windll.crypt32
    operation = library.CryptProtectData if protect else library.CryptUnprotectData
    operation.argtypes = [ctypes.POINTER(_Blob), ctypes.c_void_p,
                          ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.c_void_p,
                          wintypes.DWORD, ctypes.POINTER(_Blob)]
    operation.restype = wintypes.BOOL
    # CRYPTPROTECT_UI_FORBIDDEN; sensitive data is never displayed in a dialog.
    ok = operation(ctypes.byref(source), None, None, None, None, 1,
                   ctypes.byref(result))
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(result.pbData, result.cbData)
    finally:
        release = ctypes.windll.kernel32.LocalFree
        release.argtypes = [ctypes.c_void_p]
        release.restype = ctypes.c_void_p
        release(ctypes.cast(result.pbData, ctypes.c_void_p))


class TunnelSettings:
    """Store non-secret tunnel identity and optionally a DPAPI-encrypted key."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.config = self.directory / 'tunnel-settings.json'
        self.secret = self.directory / 'tunnel-secret.bin'

    def load(self):
        try:
            data = json.loads(self.config.read_text(encoding='utf-8'))
            tunnel_id = str(data.get('tunnel_id', ''))
            return tunnel_id if TUNNEL_ID.fullmatch(tunnel_id) else ''
        except (OSError, ValueError, TypeError):
            return ''

    def load_key(self):
        try:
            return _dpapi(self.secret.read_bytes(), False).decode('utf-8')
        except (OSError, ValueError, UnicodeError):
            return ''

    def save(self, tunnel_id, key=None, remember=False):
        if not TUNNEL_ID.fullmatch(tunnel_id):
            raise ValueError('Identificador do túnel inválido.')
        self.directory.mkdir(parents=True, exist_ok=True)
        self.config.write_text(json.dumps({'tunnel_id': tunnel_id}), encoding='utf-8')
        if remember and key:
            protected = _dpapi(key.encode('utf-8'), True)
            self.secret.write_bytes(protected)
        elif self.secret.exists():
            self.secret.unlink()

    def forget(self):
        for path in (self.secret, self.config):
            if path.exists():
                path.unlink()


class TunnelManager:
    """No PowerShell: validate, run and supervise tunnel-client in background."""

    def __init__(self, session, service, on_event=None, executable=None,
                 popen=subprocess.Popen, run=subprocess.run, clock=time.monotonic):
        self.session = session
        self.service = service
        self.on_event = on_event or (lambda event, result: None)
        self.executable = executable or bundled_tunnel_client()
        self.popen = popen
        self.run = run
        self.clock = clock
        self.lock = threading.RLock()
        self.process = None
        self.tunnel_id = ''
        self.api_key = ''
        self.enabled = False
        self.pending = False
        self.attempts = 0
        self.retry_at = 0
        self.started_at = 0
        self.connected_url = ''
        self.error = ''

    def _event(self, event, result='ok'):
        # Controlled event codes only. Never log process environment or key.
        self.on_event('tunnel.' + event, result)

    def _environment(self):
        if not self.session.status()['active'] or not self.service.ready:
            raise RuntimeError('Autorize uma sessão NavixX e aguarde MCP pronto.')
        if not self.executable or not Path(self.executable).is_file():
            raise FileNotFoundError('Cliente de túnel não encontrado no aplicativo.')
        if not TUNNEL_ID.fullmatch(self.tunnel_id):
            raise ValueError('Informe o ID válido do seu túnel OpenAI.')
        if not self.api_key or len(self.api_key.strip()) < 15:
            raise ValueError('Informe a chave OpenAI do seu próprio túnel.')
        url = f'http://127.0.0.1:{self.service.port}/mcp'
        env = os.environ.copy()
        env.update({
            'CONTROL_PLANE_API_KEY': self.api_key,
            'CONTROL_PLANE_TUNNEL_ID': self.tunnel_id,
            'MCP_SERVER_URL': url,
            'MCP_EXTRA_HEADERS': 'Authorization: Bearer ' + self.session.token,
            'MCP_DISCOVERY_EXTRA_HEADERS': 'Authorization: Bearer ' + self.session.token,
        })
        return env, url

    def configure(self, tunnel_id, api_key):
        if not TUNNEL_ID.fullmatch(tunnel_id):
            raise ValueError('O ID deve começar com tunnel_ e ter 32 dígitos hexadecimais.')
        if len(api_key.strip()) < 15:
            raise ValueError('Chave OpenAI ausente ou incompleta.')
        with self.lock:
            self.tunnel_id, self.api_key = tunnel_id, api_key.strip()
            self.enabled = True
            self.attempts = 0
            self.retry_at = 0

    def connect(self):
        """Blocking diagnostic; call from a worker thread, never Tk mainloop."""
        with self.lock:
            if self.process and self.process.poll() is None:
                return 'Túnel já está em execução.'
            if self.pending:
                return 'Conexão já está em andamento.'
            self.pending = True
        try:
            env, url = self._environment()
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            self._event('doctor_start')
            diagnostic = self.run([self.executable, 'doctor', '--explain'], env=env,
                                  capture_output=True, text=True, timeout=35,
                                  creationflags=flags)
            if diagnostic.returncode != 0 or 'RESULT ok' not in diagnostic.stdout:
                self._event('doctor_failed', 'error')
                failed = re.findall(r'^CHECK\s+([a-zA-Z0-9_-]+)\s+FAIL',
                                    (diagnostic.stdout or ''), flags=re.MULTILINE)
                checks = ', '.join(failed[:4]) if failed else 'controle de acesso ou MCP'
                raise RuntimeError(f'Diagnóstico falhou em: {checks}. Revise ID, chave e permissões OpenAI.')
            self._event('doctor_ok')
            with self.lock:
                if not self.enabled or not self.session.status()['active']:
                    return 'Sessão encerrada durante o diagnóstico.'
                self.process = self.popen([self.executable, 'run'], env=env,
                                          stdin=subprocess.DEVNULL,
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL,
                                          creationflags=flags)
                self.connected_url = url
                self.started_at = self.clock()
                self.error = ''
            self._event('started')
            return 'Túnel iniciado. Confirme o plugin uma vez no ChatGPT.'
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            # Only our controlled summary is exposed; no original CLI output.
            with self.lock:
                self.error = str(error)
                self.attempts += 1
                self.retry_at = self.clock() + _BACKOFF[min(self.attempts - 1, len(_BACKOFF) - 1)]
            self._event('start_failed', 'error')
            return self.error
        finally:
            with self.lock:
                self.pending = False

    def check(self):
        """Return a machine-checkable state and schedule safe retry if needed."""
        with self.lock:
            if not self.enabled:
                return 'desligado'
            if not self.session.status()['active']:
                self.stop()
                return 'sessão encerrada'
            if self.process:
                return_code = self.process.poll()
                if return_code is None:
                    current_url = f'http://127.0.0.1:{self.service.port}/mcp'
                    if self.service.ready and self.connected_url == current_url:
                        if self.clock() - self.started_at > 90:
                            self.attempts = 0
                        return 'executando'
                    self._terminate()
                    self.attempts = 0
                    self.retry_at = 0
                    self._event('endpoint_changed', 'warning')
                else:
                    self.process = None
                    self.attempts += 1
                    self.retry_at = self.clock() + _BACKOFF[min(self.attempts - 1, len(_BACKOFF) - 1)]
                    self._event('process_exited', 'error')
            if self.pending:
                return 'iniciando'
            if self.attempts >= 5:
                return 'falha: intervenção necessária'
            return 'reconectar' if self.clock() >= self.retry_at else 'aguardando reconexão'

    def _terminate(self):
        process = self.process
        self.process = None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill()

    def stop(self):
        with self.lock:
            self.enabled = False
            self._terminate()
            self.api_key = ''
            self.connected_url = ''
            self._event('stopped')

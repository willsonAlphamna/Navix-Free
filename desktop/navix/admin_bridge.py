"""Cloud bridge inside Navix Desktop 0.2.12; uses its real session and MCP tools."""
import ctypes
import json
import random
import os
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import threading
import time
from urllib import request, error
import webbrowser
from .tunnel_manager import _dpapi

CLOUD_URL = 'https://windows-admin-full.navixx-alfamna.workers.dev'
BRIDGE_VERSION = '0.2.0'


class AdminBridge:
    def __init__(self, session, service_getter, notify=lambda message: None):
        self.session = session
        self.service_getter = service_getter
        self.notify = notify
        self.secret = Path(session.directory) / 'admin-bridge.dpapi'
        self.pending_file = Path(session.directory) / 'admin-bridge-pending.dpapi'
        self.halt = threading.Event()
        self.enabled = threading.Event()
        self.thread = None
        self.credentials = None
        self.tools = []
        self.last_state = ''
        self.pending_result = None
        self._pair_requested = threading.Event()
        self.local_opener = request.build_opener(request.ProxyHandler({}))

    def _state(self, text):
        if text != self.last_state:
            self.last_state = text
            self.notify(text)

    def _cloud(self, path, data, authenticated=True):
        headers = {'Content-Type': 'application/json'}
        if authenticated:
            headers['Authorization'] = 'Bearer ' + self.credentials['agent_token']
        req = request.Request(CLOUD_URL + path, data=json.dumps(data).encode(), headers=headers)
        with request.urlopen(req, timeout=20) as response:
            return json.loads(response.read(2_200_000))

    def _local(self, msg):
        service = self.service_getter()
        req = request.Request('http://127.0.0.1:%d/mcp' % service.port,
            data=json.dumps(msg).encode(), headers={
                'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                'MCP-Protocol-Version': '2025-11-25',
                'Authorization': 'Bearer ' + self.session.token})
        with self.local_opener.open(req, timeout=45) as response:
            payload = json.loads(response.read(8_000_000))
        if 'error' in payload:
            raise RuntimeError('Servidor MCP local recusou a chamada')
        return payload.get('result', {})

    def _load(self):
        if self.secret.exists():
            self.credentials = json.loads(_dpapi(self.secret.read_bytes(), False).decode())
            if not isinstance(self.credentials.get('agent_token'), str):
                raise ValueError('Credencial protegida invalida')

        # Persist the result, never the remote command. An interrupted upload can
        # be repeated safely, while a Windows action must not be executed twice.
        if self.pending_file.exists():
            try:
                envelope = json.loads(_dpapi(self.pending_file.read_bytes(), False).decode())
                pending = envelope.get('pending')
                device = self.credentials.get('device_id') if self.credentials else None
                if (device is not None and envelope.get('device_id') == device
                        and isinstance(pending, dict)
                        and isinstance(pending.get('job_id'), str)
                        and pending['job_id'].startswith('job:' + device + ':')
                        and isinstance(pending.get('result'), dict)):
                    self.pending_result = pending
                else:
                    self._state('Resultado antigo de outro PC ignorado; nenhuma acao sera repetida.')
            except (OSError, ValueError, TypeError, KeyError):
                self._state('Resultado pendente nao pode ser lido; nenhuma acao sera repetida.')

    def _persist_pending(self):
        if not self.credentials or not self.pending_result:
            return
        envelope = {'device_id': self.credentials['device_id'],
                    'pending': self.pending_result}
        protected = _dpapi(json.dumps(envelope).encode(), True)
        temp = self.pending_file.with_suffix('.tmp')
        temp.write_bytes(protected)
        temp.replace(self.pending_file)

    def _clear_pending(self):
        # A 200 ack or explicit 410 expiry is required before deleting locally.
        self.pending_file.unlink(missing_ok=True)
        self.pending_result = None

    @staticmethod
    def _retry_delay(previous, exc=None):
        """Exponential backoff + jitter; honor HTTP Retry-After (seconds or date)."""
        base = min(120, max(5, previous * 2))
        header = exc.headers.get('Retry-After') if exc is not None and exc.headers else None
        if header:
            try:
                retry_seconds = max(0, int(header))
            except (TypeError, ValueError):
                try:
                    retry_seconds = max(0, (parsedate_to_datetime(header)
                         - datetime.now(timezone.utc)).total_seconds())
                except (TypeError, ValueError, OverflowError):
                    retry_seconds = 0
            base = max(base, min(3600, retry_seconds))
        return base + random.uniform(0, min(5, base * .1))

    def _enroll(self):
        enrollment = self._cloud('/device/register', {'name': os.environ.get('COMPUTERNAME', 'Meu Windows')}, False)
        self.credentials = {k: enrollment[k] for k in ('device_id', 'agent_token')}
        protected = _dpapi(json.dumps(self.credentials).encode(), True)
        temp = self.secret.with_suffix('.tmp')
        temp.write_bytes(protected)
        temp.replace(self.secret)
        webbrowser.open(enrollment['setup_url'])
        self._state('PC registrado. Autorize Windows Admin Full no navegador aberto.')

    def pair(self):
        self._pair_requested.set()

    def start(self):
        self.enabled.set()
        if self.thread and self.thread.is_alive():
            return
        self.halt.clear()
        self.thread = threading.Thread(target=self._run, daemon=True, name='navix-admin-cloud')
        self.thread.start()

    def stop(self):
        self.enabled.clear()

    def close(self):
        self.enabled.clear()
        self.halt.set()
        # Requests already accepted by the OS are not undone. Navix session.stop
        # revokes permissions and rotates its token separately in Panel.stop.

    def _run(self):
        delay = 5
        try:
            self._load()
        except Exception:
            self._state('Nao foi possivel abrir a credencial DPAPI; preserve o arquivo e confira o usuario Windows.')
            return
        while not self.halt.is_set():
            try:
                service = self.service_getter()
                if not self.enabled.is_set() or not self.session.status()['active'] or not service.ready:
                    self._state('Ponte aguardando sessao autorizada do NavixX.')
                    self.halt.wait(1)
                    continue
                if not self.credentials:
                    self._enroll()
                if self._pair_requested.is_set():
                    link = self._cloud('/device/setup', {})
                    webbrowser.open(link['setup_url'])
                    self._pair_requested.clear()
                if not self.tools:
                    self.tools = self._local({'jsonrpc':'2.0', 'id':1, 'method':'tools/list'})['tools']
                if self.pending_result:
                    self._cloud('/device/result', self.pending_result)
                    self._clear_pending()
                snapshot = self.session.status()
                snapshot.update({'administrator':bool(ctypes.windll.shell32.IsUserAnAdmin()) if os.name=='nt' else False,
                                 'bridge_version':BRIDGE_VERSION, 'native_navix':True})
                reply = self._cloud('/device/poll', {'status':snapshot, 'tools':self.tools})
                self._state('Ponte online. Vinculo ChatGPT so e comprovado ao receber uma chamada autenticada.')
                delay = 5
                if reply.get('job_id'):
                    # Never run a remote job after local stop/lock/permission revocation.
                    if self.halt.is_set() or not self.enabled.is_set() or not self.session.status()['active']:
                        result = {'isError':True,'content':[{'type':'text','text':'Acesso interrompido no NavixX.'}]}
                    else:
                        try:
                            result = self._local(reply['request'])
                        except Exception:
                            result = {'isError':True,'content':[{'type':'text','text':'Falha ou timeout no NavixX. A acao pode ter sido executada; confira antes de repetir.'}]}
                    # A pending result is retried; the underlying command is never replayed.
                    if len(json.dumps(result)) > 1_900_000:
                        result = {'isError':True,'content':[{'type':'text','text':'Resultado excede o limite de 1,9 MB. Reduza a captura ou leia arquivos menores.'}]}
                    self.pending_result = {'job_id':reply['job_id'], 'result':result}
                    self._persist_pending()
                    continue
                # Without this idle pause the worker is flooded with polls and
                # may respond 429 even while the PC and tunnel are healthy.
                self.halt.wait(5)
            except error.HTTPError as exc:
                if self.pending_result and exc.code == 410:
                    self._clear_pending()
                    self._state('Resultado expirado na nuvem; a acao nao sera repetida.')
                if exc.code in (401, 403):
                    self._state('Ponte recusou a credencial. Nenhuma acao foi executada; use diagnostico.')
                else:
                    self._state('Ponte temporariamente indisponivel; reconexao automatica.')
                delay = self._retry_delay(delay, exc)
            except Exception:
                self._state('Sem comunicacao com a ponte; reconexao automatica.')
                delay = self._retry_delay(delay)
            self.halt.wait(delay)

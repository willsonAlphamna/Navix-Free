"""Owner-authorized NavixX Cloud connection, repair and visible diagnostics.

Opening the application never authorizes remote control. After the owner
activates a local session, an already paired device may reconnect automatically.
"""
import asyncio
import threading
from urllib.error import HTTPError

from .cloud import CloudSettings
from .cloud_client import CloudRequestHandler, run_until_stopped
from .cloud_local_mcp import LocalMCPInvoker
from .cloud_pair import DeviceIdentityStore, PairingHttpClient


class CloudController:
    _MESSAGES = {
        'disconnected': 'Desconectado. Autorize uma sessão local para conectar.',
        'checking': 'Verificando o vínculo deste computador com o ChatGPT...',
        'pairing': 'Aguardando confirmação do código de vínculo no ChatGPT.',
        'unpaired': 'Computador não vinculado. Clique em Vincular ao ChatGPT uma única vez.',
        'connecting': 'Conectando ao NavixX Cloud...',
        'connected': 'Canal com a nuvem ativo. Falta confirmar uma chamada real no ChatGPT.',
        'verified': 'Comunicação remota confirmada: uma ferramenta respondeu ao ChatGPT.',
        'retrying': 'Comunicação interrompida. Reconexão automática em {seconds}s.',
        'network_error': 'Sem resposta da nuvem. Verifique a internet e tente Reparar conexão.',
        'authorization_required': 'Vínculo recusado ou expirado. Vincule o computador novamente.',
        'local_expired': 'Autorização local encerrada. Clique em Conectar / Autorizar.',
        'local_starting': 'Iniciando servidor MCP local. Aguarde...',
        'stopped': 'Desconectado pelo proprietário.',
    }

    def __init__(self, directory, session, service, relay_url, on_status=None):
        self.settings=CloudSettings(enabled=True,relay_url=relay_url)
        self.identity_store=DeviceIdentityStore(directory)
        self.session=session
        self.service=service
        self.on_status=on_status or (lambda message: None)
        self.thread=None
        self.loop=None
        self.stop_event=None
        self.lock=threading.Lock()
        self._stop_requested=threading.Event()
        self._state='disconnected'
        self._message=self._MESSAGES['disconnected']

    def status(self):
        """Local snapshot only; UI polling never makes a network request."""
        with self.lock:
            return {'state': self._state, 'message': self._message,
                    'running': bool(self.thread and self.thread.is_alive())}

    @property
    def port(self):
        """Always use the current local MCP port, even after repair."""
        return self.service.port

    @property
    def ready(self):
        return self.service.ready

    def _set_state(self, state, seconds=0):
        if self._stop_requested.is_set() and state != 'stopped':
            return  # A late WebSocket/call callback must not undo PARAR ACESSO.
        message=self._MESSAGES[state].format(seconds=seconds)
        with self.lock:
            changed=self._state != state or self._message != message
            self._state=state
            self._message=message
        if changed:
            self.on_status('NavixX Cloud: ' + message)

    def enroll(self):
        self.settings.validate()
        if not self.session.status().get('active'):
            raise PermissionError('Autorize uma sessão local antes de parear.')
        identity=self.identity_store.ensure()
        client=PairingHttpClient(self.settings)
        data=client.renew(identity) if client.status(identity) else client.begin(identity)
        self._set_state('pairing')
        return data

    def paired(self):
        identity=self.identity_store.load()
        return bool(identity and PairingHttpClient(self.settings).status(identity))

    def start(self):
        try:
            self.settings.validate()
        except ValueError:
            self._set_state('network_error')
            raise
        if not self.session.status().get('active'):
            self._set_state('local_expired')
            raise PermissionError('Autorize primeiro uma sessão local.')
        if not self.service.ready:
            self._set_state('local_starting')
            raise PermissionError('O servidor MCP local ainda está iniciando.')
        with self.lock:
            if self.thread and self.thread.is_alive():
                return False
        identity=self.identity_store.load()
        if not identity:
            self._set_state('unpaired')
            raise PermissionError('O computador ainda não foi vinculado à sua conta.')
        self._set_state('checking')
        try:
            linked=PairingHttpClient(self.settings).status(identity)
        except HTTPError as error:
            if error.code in (401, 403, 404):
                self._set_state('authorization_required')
                raise PermissionError('O vínculo Cloud foi recusado. Vincule novamente.') from error
            self._set_state('network_error')
            raise ConnectionError('O serviço Cloud não respondeu como esperado.') from error
        except Exception as error:
            self._set_state('network_error')
            raise ConnectionError('Não foi possível verificar o vínculo com a nuvem.') from error
        if not linked:
            self._set_state('unpaired')
            raise PermissionError('Vínculo ausente ou expirado. Clique em Vincular ao ChatGPT.')
        if not self.session.status().get('active'):
            self._set_state('local_expired')
            raise PermissionError('A autorização local expirou durante a conexão.')
        with self.lock:
            if self.thread and self.thread.is_alive():
                return False
            self._stop_requested.clear()
            self.thread=threading.Thread(target=self._run,args=(identity,),daemon=True,
                                         name='NavixCloudClient')
            worker=self.thread
        self._set_state('connecting')
        worker.start()
        return True

    def _run(self, identity):
        if self._stop_requested.is_set():
            self._set_state('stopped')
            return
        async def main():
            self.loop=asyncio.get_running_loop()
            self.stop_event=asyncio.Event()
            # This controller is a live service reference. LocalMCPInvoker
            # therefore follows a replaced MCP server and its random port.
            handler=CloudRequestHandler(self.session,
                                        invoke=LocalMCPInvoker(self.session,self),
                                        on_success=lambda tool: self._set_state('verified'))
            try:
                await run_until_stopped(self.settings,identity.device_id,
                                        lambda:identity.agent_secret,handler,self.stop_event,
                                        on_state=self._set_state)
            finally:
                self.loop=None
                self.stop_event=None
        try:
            asyncio.run(main())
        except Exception:
            self._set_state('network_error')
        finally:
            state=self.status()['state']
            if self._stop_requested.is_set():
                self._set_state('stopped')
            elif state not in ('authorization_required', 'local_expired', 'unpaired',
                               'network_error'):
                self._set_state('disconnected')

    def stop(self):
        self._stop_requested.set()
        with self.lock:
            loop=self.loop
            stop_event=self.stop_event
            if loop and stop_event and loop.is_running():
                loop.call_soon_threadsafe(stop_event.set)
        self._set_state('stopped')
        return True

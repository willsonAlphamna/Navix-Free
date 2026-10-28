"""Owner-initiated NavixX Cloud lifecycle, separate from the 0.2.11 tunnel.

A future UI explicitly calls enroll/start/stop. Merely installing the app,
opening it, or importing this module never starts a remote-control channel.
"""
import asyncio
import threading

from .cloud import CloudSettings
from .cloud_client import CloudRequestHandler, run_until_stopped
from .cloud_local_mcp import LocalMCPInvoker
from .cloud_pair import DeviceIdentityStore, PairingHttpClient


class CloudController:
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

    def enroll(self):
        self.settings.validate()
        if not self.session.status().get('active'):
            raise PermissionError('Autorize uma sessão local antes de parear.')
        identity=self.identity_store.ensure()
        return PairingHttpClient(self.settings).begin(identity)

    def paired(self):
        identity=self.identity_store.load()
        return bool(identity and PairingHttpClient(self.settings).status(identity))

    def start(self):
        self.settings.validate()
        if not self.session.status().get('active') or not self.service.ready:
            raise PermissionError('Conecte primeiro o servidor MCP local.')
        identity=self.identity_store.load()
        if not identity or not PairingHttpClient(self.settings).status(identity):
            raise PermissionError('O computador ainda não foi vinculado à sua conta.')
        with self.lock:
            if self.thread and self.thread.is_alive():
                return False
            self.thread=threading.Thread(target=self._run,args=(identity,),daemon=True,
                                         name='NavixCloudClient')
            self.thread.start()
        return True

    def _run(self, identity):
        async def main():
            self.loop=asyncio.get_running_loop()
            self.stop_event=asyncio.Event()
            handler=CloudRequestHandler(self.session,
                                        invoke=LocalMCPInvoker(self.session,self.service))
            self.on_status('NavixX Cloud: sessão iniciada pelo proprietário.')
            try:
                await run_until_stopped(self.settings,identity.device_id,
                                        lambda:identity.agent_secret,handler,self.stop_event)
            finally:
                self.on_status('NavixX Cloud: conexão encerrada.')
                self.loop=None
                self.stop_event=None
        asyncio.run(main())

    def stop(self):
        with self.lock:
            loop=self.loop
            stop_event=self.stop_event
            if loop and stop_event and loop.is_running():
                loop.call_soon_threadsafe(stop_event.set)
            return True

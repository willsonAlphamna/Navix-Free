import asyncio
import json
import unittest
from navix.cloud import CloudSettings
from navix.cloud_client import CloudRequestHandler, connect_once, device_url, run_until_stopped


class FakeSession:
    def __init__(self, active=True, perms=()):
        self.active = active
        self.perms = set(perms)
    def status(self):
        return {'active': self.active, 'permissions': sorted(self.perms)}
    def require(self, capability):
        if capability not in self.perms:
            raise PermissionError(capability)


class FakeSocket:
    def __init__(self, incoming):
        self.incoming = incoming
        self.sent = []
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        return None
    def __aiter__(self):
        self.iterator = iter(self.incoming)
        return self
    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration:
            raise StopAsyncIteration
    async def send(self, text):
        self.sent.append(json.loads(text))


def call(tool='status', args=None, deadline=2000):
    return json.dumps({'kind': 'call', 'id': '12345678-1234-1234-1234-123456789012',
                       'tool': tool, 'args': {} if args is None else args,
                       'deadline': deadline})


class CloudClientTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.settings = CloudSettings(enabled=True, relay_url='wss://navixx.example/api/device/connect')
        self.session = FakeSession(perms=['browser', 'desktop', 'files'])
        self.handler = CloudRequestHandler(self.session, clock=lambda: 1)

    async def test_status_does_not_require_device_permission(self):
        result = json.loads(await self.handler.handle(call()))
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['active'], True)

    async def test_remote_call_denied_without_local_permission(self):
        result = json.loads(await self.handler.handle(call('command_run', {'command':'test'})))
        self.assertFalse(result['ok'])

    async def test_remote_call_denied_when_session_revoked(self):
        self.session.active = False
        result = json.loads(await self.handler.handle(call('desktop_click', {'x':1,'y':1})))
        self.assertFalse(result['ok'])

    async def test_whitelist_rejects_unregistered_tool(self):
        result = json.loads(await self.handler.handle(call('shell_root')))
        self.assertFalse(result['ok'])

    async def test_expired_and_malformed_envelopes(self):
        for payload in [call(deadline=10), 'not-json', json.dumps([]), 'x'*270000]:
            self.assertFalse(json.loads(await self.handler.handle(payload))['ok'])

    async def test_dispatch_requires_explicit_handler(self):
        result = json.loads(await self.handler.handle(call('files_read', {'path':'x'})))
        self.assertFalse(result['ok'])

    async def test_explicit_handler_dispatches_only_with_permissions(self):
        async def invoke(name, args):
            return {'tool':name,'args':args}
        self.handler.invoke = invoke
        reply = json.loads(await self.handler.handle(call('files_read', {'path':'teste'})))
        self.assertTrue(reply['ok'])
        self.assertEqual(reply['result']['args']['path'],'teste')

    async def test_device_url_uses_wss_and_never_embeds_token(self):
        url = device_url(self.settings,'device_1234567890')
        self.assertEqual(url,'wss://navixx.example/api/device/connect?device_id=device_1234567890')
        with self.assertRaises(ValueError):
            device_url(self.settings,'../outra-rota')

    async def test_connect_once_sends_agent_secret_only_in_header(self):
        socket = FakeSocket([call()])
        captured = {}
        def fake_connect(url, **options):
            captured.update({'url':url, **options})
            return socket
        await connect_once(self.settings,'device_1234567890',lambda: 'a'*43,
                           self.handler,websocket_connect=fake_connect)
        self.assertEqual(captured['additional_headers']['X-Navix-Agent-Token'],'a'*43)
        self.assertNotIn('a'*43,captured['url'])
        self.assertTrue(socket.sent[0]['ok'])

    async def test_refuses_missing_agent_token_before_connect(self):
        with self.assertRaises(PermissionError):
            await connect_once(self.settings,'device_1234567890',lambda: '',self.handler,
                               websocket_connect=lambda *a,**kw: None)

    async def test_stop_cancels_active_websocket_immediately(self):
        started=asyncio.Event()
        cancelled=asyncio.Event()
        stop=asyncio.Event()
        async def fake_connect(*args):
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise
        runner=asyncio.create_task(run_until_stopped(
            self.settings,'device_1234567890',lambda:'a'*43,
            self.handler,stop,connect=fake_connect))
        await asyncio.wait_for(started.wait(),1)
        stop.set()
        await asyncio.wait_for(runner,1)
        self.assertTrue(cancelled.is_set())


if __name__=='__main__':
    unittest.main()

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

    async def test_only_a_successful_remote_call_confirms_end_to_end(self):
        calls=[]
        handler=CloudRequestHandler(self.session,clock=lambda:1,
                                    on_success=lambda tool:calls.append(tool))
        self.assertTrue(json.loads(await handler.handle(call()))['ok'])
        self.assertEqual(calls,['status'])
        self.assertFalse(json.loads(await handler.handle(call('command_run')))['ok'])
        self.assertEqual(calls,['status'])

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
        for payload in [call(deadline=-150000), call(deadline=185000),
                        'not-json', json.dumps([]), 'x'*9_000_000]:
            self.assertFalse(json.loads(await self.handler.handle(payload))['ok'])

    async def test_cloud_command_accepts_moderate_windows_clock_skew(self):
        # Worker timestamps are UTC. The PC can be ~45s behind the edge;
        # its 30s command deadline would otherwise look >60s in the future.
        for clock_offset_seconds in (-90, 90):
            handler = CloudRequestHandler(self.session,
                                          clock=lambda: 1000+clock_offset_seconds)
            msg = call(deadline=1030000)
            result = json.loads(await handler.handle(msg))
            self.assertTrue(result['ok'],f'Clock offset {clock_offset_seconds}s')

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
        states = []
        def fake_connect(url, **options):
            captured.update({'url':url, **options})
            return socket
        await connect_once(self.settings,'device_1234567890',lambda: 'a'*43,
                           self.handler,websocket_connect=fake_connect,
                           on_connected=lambda: states.append('connected'))
        self.assertEqual(captured['additional_headers']['X-Navix-Agent-Token'],'a'*43)
        self.assertEqual(captured['user_agent_header'],'NavixX-Desktop-Cloud/0.3.0')
        self.assertNotIn('a'*43,captured['url'])
        self.assertTrue(socket.sent[0]['ok'])
        self.assertEqual(states, ['connected'])

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

    async def test_permission_error_stops_and_explains_why(self):
        states=[]
        attempts=[]
        async def invalid(*args):
            attempts.append('try')
            raise PermissionError('secret value must not be shown')
        await run_until_stopped(self.settings,'device_1234567890',lambda:'a'*43,
                                self.handler,asyncio.Event(),connect=invalid,
                                on_state=lambda state,seconds: states.append((state,seconds)))
        self.assertEqual(len(attempts),1)
        self.assertEqual(states[-1][0],'authorization_required')
        self.assertNotIn('secret value',str(states))

    async def test_expired_local_authorization_does_not_reconnect(self):
        self.session.active=False
        states=[]
        await run_until_stopped(self.settings,'device_1234567890',lambda:'a'*43,
                                self.handler,asyncio.Event(),
                                on_state=lambda state,seconds: states.append(state))
        self.assertEqual(states,['local_expired'])

    async def test_transient_failure_retries_and_reports_backoff(self):
        attempts=[]
        states=[]
        connected=asyncio.Event()
        stop=asyncio.Event()
        async def flaky(*args):
            attempts.append('try')
            if len(attempts)==1:
                raise OSError('internet offline')
            connected.set()
            await asyncio.Event().wait()
        runner=asyncio.create_task(run_until_stopped(
            self.settings,'device_1234567890',lambda:'a'*43,
            self.handler,stop,connect=flaky,
            on_state=lambda state,seconds: states.append((state,seconds))))
        await asyncio.wait_for(connected.wait(),3)
        stop.set()
        await asyncio.wait_for(runner,1)
        self.assertEqual(len(attempts),2)
        self.assertIn(('retrying',1),states)

    async def test_relay_refusing_device_requires_new_authorization(self):
        class Refused(Exception):
            response=type('Response',(),{'status_code':403})()
        states=[]
        async def denied(*args):
            raise Refused('no raw error in the UI')
        await run_until_stopped(self.settings,'device_1234567890',lambda:'a'*43,
                                self.handler,asyncio.Event(),connect=denied,
                                on_state=lambda state,seconds: states.append(state))
        self.assertEqual(states[-1],'authorization_required')


if __name__=='__main__':
    unittest.main()

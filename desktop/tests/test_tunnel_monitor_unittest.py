"""Fast offline reliability checks runnable even without pytest installed."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock
from uuid import uuid4

from navix.tunnel_manager import (
    TunnelManager, _local_health_base, _health_snapshot,
)


TUNNEL_ID = 'tunnel_' + 'b' * 32


class Process:
    def __init__(self):
        self.dead = False

    def poll(self):
        return 0 if self.dead else None

    def terminate(self):
        self.dead = True

    def wait(self, timeout=0):
        return 0


class Reply:
    status = 200

    def __init__(self, data=b'live'):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _):
        return self.data


class TunnelReliabilityTests(unittest.TestCase):
    def make_tunnel(self):
        def fake_health_file(**_):
            read_fd, write_fd = os.pipe()
            os.close(read_fd)
            return write_fd, '/tmp/navix-test-' + uuid4().hex + '.url'

        patcher = mock.patch('navix.tunnel_manager.tempfile.mkstemp',
                             side_effect=fake_health_file)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.process = Process()
        self.events = []
        self.calls = []
        session = SimpleNamespace(token='LOCAL_PRIVATE_TOKEN',
                                  status=lambda: {'active': True})
        service = SimpleNamespace(ready=True, port=42424)

        def diagnose(args, **options):
            self.calls.append((args, options))
            return SimpleNamespace(returncode=0, stdout='RESULT ok\n')

        def run_client(args, **options):
            self.calls.append((args, options))
            return self.process

        tunnel = TunnelManager(
            session, service, on_event=lambda *args: self.events.append(args),
            executable=__file__, run=diagnose, popen=run_client,
        )
        tunnel.configure(TUNNEL_ID, 'sk-private-test-not-a-real-key')
        return tunnel

    def test_rejects_remote_health_probe(self):
        self.assertEqual(_local_health_base('http://127.0.0.1:42/healthz'),
                         'http://127.0.0.1:42')
        for address in ['https://127.0.0.1:42/healthz',
                        'http://attacker.example:42/readyz',
                        'http://127.0.0.1.attacker:42',
                        'http://username@localhost:42',
                        'http://[invalid:42/']:
            self.assertEqual(_local_health_base(address), '')

    def test_health_probes_and_remote_degradation(self):
        class FakeOpener:
            def __init__(self):
                self.mode = 'ready'

            def open(self, url, timeout=None):
                if url.endswith('/readyz') and self.mode == 'pending':
                    from urllib.error import HTTPError
                    raise HTTPError(url, 503, 'not ready', {}, None)
                if '/health?' in url:
                    payload = json.dumps({'components': {'control-plane': {
                        'status': 'degraded' if self.mode == 'degraded' else 'ok'
                    }}}).encode()
                    return Reply(payload)
                return Reply()

        opener = FakeOpener()
        with mock.patch('navix.tunnel_manager.urlrequest.build_opener',
                        return_value=opener):
            self.assertEqual(_health_snapshot('http://127.0.0.1:42'), 'ready')
            opener.mode = 'degraded'
            self.assertEqual(_health_snapshot('http://127.0.0.1:42'), 'remote_degraded')
            opener.mode = 'pending'
            self.assertEqual(_health_snapshot('http://127.0.0.1:42'), 'starting')

    def test_process_alive_does_not_claim_chatgpt_online(self):
        tunnel = self.make_tunnel()
        self.assertIn('iniciado', tunnel.connect())
        self.assertIn('não verificada', tunnel.check())
        self.assertEqual(tunnel.health_state, 'unknown')
        self.assertEqual(len(self.calls), 2)
        self.assertIn('HEALTH_URL_FILE', self.calls[1][1]['env'])
        self.assertNotIn('LOCAL_PRIVATE_TOKEN', str(self.calls[1][0]))
        self.assertNotIn('sk-private-test-not-a-real-key', str(self.calls[1][0]))
        health_path = Path(self.calls[1][1]['env']['HEALTH_URL_FILE'])
        tunnel.stop()
        self.assertFalse(health_path.exists())

    def test_manual_repair_preserves_authorized_key(self):
        tunnel = self.make_tunnel()
        tunnel.connect()
        self.assertTrue(tunnel.request_reconnect())
        self.assertTrue(self.process.dead)
        self.assertEqual(tunnel.check(), 'reconectar')
        self.assertEqual(tunnel.api_key, 'sk-private-test-not-a-real-key')
        tunnel.stop()

    def test_transient_retry_continues_but_bad_credentials_stop(self):
        tunnel = self.make_tunnel()
        tunnel.attempts = 17
        tunnel.retry_at = 0
        self.assertEqual(tunnel.check(), 'reconectar')
        tunnel.last_reason = 'Credencial do túnel recusada (401).'
        self.assertEqual(tunnel.check(), 'falha: intervenção necessária')

    def test_unresponsive_health_listener_restarts_client_with_backoff(self):
        tunnel = self.make_tunnel()
        current_time = [1000]
        tunnel.clock = lambda: current_time[0]
        with mock.patch('navix.tunnel_manager.threading.Thread'):
            tunnel.connect()
        process = self.process

        def advance(_):
            current_time[0] += 7

        with mock.patch.object(Path, 'read_text',
                               return_value='http://127.0.0.1:42/healthz'), \
                mock.patch('navix.tunnel_manager._health_snapshot',
                           return_value='health_failed'), \
                mock.patch('navix.tunnel_manager.time.sleep',
                           side_effect=advance):
            tunnel._health_watch(process)
        self.assertTrue(process.dead)
        self.assertEqual(tunnel.attempts, 1)
        self.assertGreater(tunnel.retry_at, current_time[0])
        self.assertEqual(tunnel.check(), 'aguardando reconexão')
        self.assertIn(('tunnel.health_restart', 'warning'), self.events)


if __name__ == '__main__':
    unittest.main()

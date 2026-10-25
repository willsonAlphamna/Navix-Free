"""Secure tunnel orchestration; no OpenAI credentials required in CI."""
from types import SimpleNamespace
import sys

import pytest

from navix.tunnel_manager import TunnelManager, TunnelSettings, TUNNEL_ID


ID = 'tunnel_' + 'a' * 32


class FakeProcess:
    def __init__(self):
        self.terminated = False

    def poll(self):
        return 0 if self.terminated else None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=0):
        return 0


def manager(run_result='RESULT ok\n'):
    calls = []
    child = FakeProcess()
    session = SimpleNamespace(token='NAVIX_SECRET_BEARER',
                              status=lambda: {'active': True, 'permissions': ['browser']})
    service = SimpleNamespace(ready=True, port=3180)
    def run(args, **kwargs):
        calls.append(('doctor', args, kwargs))
        return SimpleNamespace(returncode=0 if 'RESULT ok' in run_result else 1,
                               stdout=run_result)
    def popen(args, **kwargs):
        calls.append(('run', args, kwargs))
        return child
    events = []
    tunnel = TunnelManager(session, service, on_event=lambda *e: events.append(e),
                           executable=sys.executable, popen=popen, run=run)
    return tunnel, calls, child, events


def test_tunnel_setup_uses_environment_not_secrets_in_argv():
    tunnel, calls, child, events = manager()
    tunnel.configure(ID, 'sk-test-long-private-key-value')
    assert 'Túnel iniciado' in tunnel.connect()
    assert tunnel.check() == 'executando'
    assert len(calls) == 2
    for _, argv, options in calls:
        assert 'sk-test-long-private-key-value' not in str(argv)
        assert 'NAVIX_SECRET_BEARER' not in str(argv)
        assert options['env']['CONTROL_PLANE_API_KEY'] == 'sk-test-long-private-key-value'
        assert options['env']['MCP_SERVER_URL'] == 'http://127.0.0.1:3180/mcp'
        assert options['env']['MCP_EXTRA_HEADERS'] == 'Authorization: Bearer NAVIX_SECRET_BEARER'
    assert ('tunnel.started', 'ok') in events
    tunnel.stop()
    assert child.terminated
    assert tunnel.api_key == ''


def test_tunnel_rejects_invalid_identity():
    tunnel, calls, _, _ = manager()
    with pytest.raises(ValueError):
        tunnel.configure('tunnel_INVALID', 'sk-long-key-123456')
    assert not calls
    assert TUNNEL_ID.fullmatch(ID)


def test_tunnel_diagnostic_failure_never_starts_process():
    tunnel, calls, _, events = manager('RESULT fail\n')
    tunnel.configure(ID, 'sk-test-long-private-key-value')
    assert 'falhou' in tunnel.connect()
    assert len(calls) == 1
    assert ('tunnel.start_failed', 'error') in events


def test_service_port_change_requires_reconnect():
    tunnel, calls, child, _ = manager()
    tunnel.configure(ID, 'sk-test-long-private-key-value')
    tunnel.connect()
    tunnel.service.port = 6550
    assert tunnel.check() == 'reconectar'
    assert child.terminated


def test_settings_do_not_save_plaintext_key_by_default(tmp_path):
    prefs = TunnelSettings(tmp_path)
    prefs.save(ID, 'sk-do-not-write-this-secret', remember=False)
    assert prefs.load() == ID
    assert not prefs.secret.exists()
    assert 'sk-do-not-write-this-secret' not in prefs.config.read_text()


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows DPAPI only')
def test_dpapi_secret_roundtrip_current_windows_account(tmp_path):
    prefs = TunnelSettings(tmp_path)
    prefs.save(ID, 'sk-unique-private-credential', remember=True)
    assert prefs.load_key() == 'sk-unique-private-credential'
    assert b'sk-unique-private-credential' not in prefs.secret.read_bytes()
    prefs.forget()
    assert not prefs.secret.exists()

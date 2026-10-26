"""Secure tunnel orchestration; no OpenAI credentials required in CI."""
from types import SimpleNamespace
import sys

import pytest

from navix.tunnel_manager import (
    TunnelManager, TunnelSettings, TUNNEL_ID, _diagnose_runtime_line,
    _local_health_base, _health_snapshot,
)


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
    assert 'ChatGPT' in tunnel.check() or 'conexão externa não verificada' in tunnel.check()
    assert len(calls) == 2
    for _, argv, options in calls:
        assert 'sk-test-long-private-key-value' not in str(argv)
        assert 'NAVIX_SECRET_BEARER' not in str(argv)
        assert options['env']['CONTROL_PLANE_API_KEY'] == 'sk-test-long-private-key-value'
        assert options['env']['MCP_SERVER_URL'] == 'http://127.0.0.1:3180/mcp'
        assert options['env']['MCP_EXTRA_HEADERS'] == 'Authorization: Bearer NAVIX_SECRET_BEARER'
        assert options['env']['HEALTH_LISTEN_ADDR'] == '127.0.0.1:0'
        assert options['env']['HEALTH_URL_FILE'].endswith('.url')
    assert ('tunnel.started', 'ok') in events
    tunnel.stop()
    assert child.terminated
    assert tunnel.api_key == ''


def test_health_listener_rejects_non_loopback_or_untrusted_urls():
    assert _local_health_base('http://127.0.0.1:62880/healthz') == 'http://127.0.0.1:62880'
    assert _local_health_base('http://[::1]:62880/healthz') == 'http://[::1]:62880'
    for address in ('https://127.0.0.1:80/healthz', 'http://example.com:80',
                    'http://127.0.0.1.example.com:80', 'file:///tmp/healthz',
                    'http://127.0.0.1:bad/healthz'):
        assert _local_health_base(address) == ''


def test_health_snapshot_classifies_ready_gated_and_degraded(monkeypatch):
    import json
    from navix import tunnel_manager

    class Response:
        status = 200
        def __init__(self, payload):
            self.payload = payload
        def __enter__(self):
            return self
        def __exit__(self, *_):
            pass
        def read(self, _):
            return self.payload

    class FakeOpener:
        def __init__(self):
            self.degraded = False
            self.not_ready = False
        def open(self, url, timeout=0):
            assert url.startswith('http://127.0.0.1:42/')
            if '/readyz' in url and self.not_ready:
                raise tunnel_manager.urlerror.HTTPError(url, 503, 'pending', {}, None)
            if '/health?' in url:
                return Response(json.dumps({'components': {
                    'control-plane': {'status': 'degraded' if self.degraded else 'ok'}
                }}).encode())
            return Response(b'live')

    fake = FakeOpener()
    monkeypatch.setattr(tunnel_manager.urlrequest, 'build_opener', lambda *_: fake)
    assert _health_snapshot('http://127.0.0.1:42') == 'ready'
    fake.degraded = True
    assert _health_snapshot('http://127.0.0.1:42') == 'remote_degraded'
    fake.not_ready = True
    assert _health_snapshot('http://127.0.0.1:42') == 'starting'


def test_repair_preserves_credentials_and_retries():
    tunnel, _, child, _ = manager()
    tunnel.configure(ID, 'sk-test-long-private-key-value')
    tunnel.connect()
    assert tunnel.request_reconnect()
    assert child.terminated
    assert tunnel.api_key == 'sk-test-long-private-key-value'
    assert tunnel.check() == 'reconectar'


def test_transient_retry_is_not_abandoned_after_five_attempts():
    tunnel, _, _, _ = manager()
    tunnel.configure(ID, 'sk-test-long-private-key-value')
    tunnel.attempts = 12
    tunnel.retry_at = 0
    assert tunnel.check() == 'reconectar'
    tunnel.error = 'Diagnóstico falhou em: authentication'
    assert tunnel.check() == 'falha: intervenção necessária'


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


def test_runtime_errors_are_classified_without_copying_secret_data():
    assert '401' in _diagnose_runtime_line('HTTP 401: invalid runtime key sk-sensitive-secret')
    assert '403' in _diagnose_runtime_line('request failed status 403 Forbidden')
    assert 'Porta' in _diagnose_runtime_line('listen tcp: bind: address already in use')
    assert 'cloudflared' in _diagnose_runtime_line('cloudflared.exe not found')
    assert _diagnose_runtime_line('my secret sk-sensitive-secret') == ''


def test_inherited_manual_profile_is_not_reused(monkeypatch):
    monkeypatch.setenv('TUNNEL_CLIENT_PROFILE', 'old-navix')
    monkeypatch.setenv('TUNNEL_CLIENT_CONFIG', 'C:/old-config.yaml')
    tunnel, calls, _, _ = manager()
    tunnel.configure(ID, 'sk-test-long-private-key-value')
    tunnel.connect()
    assert 'TUNNEL_CLIENT_PROFILE' not in calls[0][2]['env']
    assert 'TUNNEL_CLIENT_CONFIG' not in calls[0][2]['env']


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

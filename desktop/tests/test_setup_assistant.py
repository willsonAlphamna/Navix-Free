from types import SimpleNamespace
from navix.core import Session
from navix.setup_assistant import local_diagnostic, find_tunnel_client


def test_diagnostic_never_reports_remote_connection(tmp_path, monkeypatch):
    session = Session(tmp_path)
    service = SimpleNamespace(ready=True, port=34567)
    panel = SimpleNamespace(session=session, service=service)
    monkeypatch.setattr('navix.setup_assistant.find_tunnel_client', lambda: None)
    result = local_diagnostic(panel)
    assert result['server_ready']
    assert not result['session_active']
    assert result['port'] == 34567
    assert not result['tunnel_client_found']
    session.activate(['browser', 'files'])
    result = local_diagnostic(panel)
    assert result['session_active']
    assert result['permissions'] == ['browser', 'files']


def test_tunnel_missing_is_normal(tmp_path, monkeypatch):
    monkeypatch.setattr('navix.setup_assistant.shutil.which', lambda name: None)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    assert find_tunnel_client() is None

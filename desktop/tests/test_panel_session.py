from types import SimpleNamespace

from navix.core import Session
from navix.gui import Panel


def panel(tmp_path, ready=True, alive=True):
    now = [0]
    session = Session(tmp_path, clock=lambda: now[0])
    messages = []
    service = SimpleNamespace(ready=ready, thread=SimpleNamespace(is_alive=lambda: alive))
    return SimpleNamespace(session=session, service=service, show=messages.append,
                           browser=object(), busy=False), now, messages


def test_repair_preserves_authorization_token_and_original_expiry(tmp_path):
    ui, now, messages = panel(tmp_path)
    ui.session.activate(['browser', 'desktop'])
    token = ui.session.token
    now[0] = 600
    Panel.repair(ui)
    assert ui.session.token == token
    assert ui.session.status() == {'active': True, 'remaining_seconds': 1200,
                                   'permissions': ['browser', 'desktop']}


def test_repair_does_not_authorize_stopped_session(tmp_path):
    ui, _, messages = panel(tmp_path)
    ui.session.activate(['browser'])
    ui.session.stop()
    token = ui.session.token
    Panel.repair(ui)
    assert not ui.session.status()['active']
    assert ui.session.token == token
    assert any('Conectar / Autorizar' in message for message in messages)


def test_repair_waits_for_starting_server_without_revoking(tmp_path):
    ui, _, _ = panel(tmp_path, ready=False)
    ui.session.activate(['browser'])
    token = ui.session.token
    Panel.repair(ui)
    assert ui.session.authenticates(token)
    assert ui.session.status()['active']


def test_repair_restarts_dead_service_without_extending_session(tmp_path, monkeypatch):
    ui, now, messages = panel(tmp_path, ready=False, alive=False)
    ui.session.activate(['browser'])
    now[0] = 120
    token = ui.session.token
    calls = []
    ui.service.close = lambda: calls.append('close')
    replacement = SimpleNamespace(start=lambda: calls.append('start'))
    monkeypatch.setattr('navix.gui.Service', lambda *args, **kwargs: replacement)
    Panel.repair(ui)
    assert calls == ['close', 'start']
    assert ui.service is replacement
    assert ui.session.authenticates(token)
    assert ui.session.status()['remaining_seconds'] == 1680


def test_open_browser_explains_missing_authorization_without_launching(tmp_path):
    ui, _, messages = panel(tmp_path)
    Panel.open_browser(ui, 'integrado')
    assert not ui.busy
    assert 'Conectar / Autorizar' in messages[-1]


def test_open_browser_does_not_grant_browser_permission(tmp_path):
    ui, _, messages = panel(tmp_path)
    ui.session.activate(['desktop'])
    Panel.open_browser(ui, 'integrado')
    assert not ui.busy
    assert ui.session.status()['permissions'] == ['desktop']


def test_connect_uses_explicit_file_and_command_choices(tmp_path):
    ui, _, messages = panel(tmp_path)
    class Flag:
        def __init__(self, value): self.value = value
        def get(self): return self.value
    ui.browser_allowed = Flag(False)
    ui.desktop_allowed = Flag(False)
    ui.files_allowed = Flag(True)
    ui.commands_allowed = Flag(True)
    started = []
    ui.service.start = lambda: started.append(True)
    Panel.connect(ui)
    assert started == [True]
    assert ui.session.status()['permissions'] == ['commands', 'files']

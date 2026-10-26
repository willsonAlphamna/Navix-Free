"""Validate native-action dispatch without moving this test machine's mouse."""
import io
import sys
from types import SimpleNamespace

import pytest

from navix.core import Session
from navix.desktop import Desktop


@pytest.fixture
def setup(tmp_path, monkeypatch):
    calls = []

    def record(name):
        def method(*args, **kwargs):
            calls.append((name, args, kwargs))
        return method

    pg = SimpleNamespace(
        size=lambda: (1920, 1080), position=lambda: (101, 202),
        KEYBOARD_KEYS=['enter', 'tab', 'esc', 'ctrl', 'shift', 'win', 'f5', 'a', 'delete'],
        click=record('click'), moveTo=record('move'), dragTo=record('drag'),
        press=record('key'), keyDown=record('down'), keyUp=record('up'), scroll=record('scroll'),
    )
    monkeypatch.setitem(sys.modules, 'pyautogui', pg)
    session = Session(tmp_path)
    session.activate(['desktop'])
    return Desktop(session), session, pg, calls


def test_position_and_screen_info(setup):
    desktop, _, _, calls = setup
    assert desktop.call('position') == {'x': 101, 'y': 202}
    assert desktop.call('screen_info') == {'width': 1920, 'height': 1080, 'x': 101, 'y': 202}
    assert calls == []


def test_motion_and_double_right_click(setup):
    desktop, _, pg, calls = setup
    assert desktop.call('move', x=100, y=200) == {'ok': True}
    desktop.call('drag', x=300, y=400, duration=1, button='middle')
    desktop.call('click', x=100, y=200, button='right', clicks=2)
    assert calls == [
        ('move', (100, 200), {'duration': .2}),
        ('drag', (300, 400), {'duration': 1, 'button': 'middle'}),
        ('click', (100, 200), {'button': 'right', 'clicks': 2, 'interval': .1}),
    ]
    assert pg.FAILSAFE is True


def test_hotkeys_and_function_keys(setup):
    desktop, _, _, calls = setup
    desktop.call('hotkey', keys=['Ctrl', 'Shift', 'a'])
    desktop.call('key', key='F5')
    assert calls == [
        ('down', ('ctrl',), {'_pause': False}),
        ('down', ('shift',), {'_pause': False}),
        ('down', ('a',), {'_pause': False}),
        ('up', ('a',), {'_pause': False}),
        ('up', ('shift',), {'_pause': False}),
        ('up', ('ctrl',), {'_pause': False}),
        ('key', ('f5',), {}),
    ]


def test_revoking_during_chord_releases_pressed_modifier(setup):
    desktop, session, pg, calls = setup

    def key_down(key, **kwargs):
        calls.append(('down', key))
        session.stop()

    def key_up(key, **kwargs):
        assert pg.FAILSAFE is False  # Release only; no new input is injected.
        calls.append(('up', key))

    pg.keyDown = key_down
    pg.keyUp = key_up
    with pytest.raises(PermissionError):
        desktop.call('hotkey', keys=['ctrl', 'a'])
    assert calls == [('down', 'ctrl'), ('up', 'ctrl')]
    assert pg.FAILSAFE is True


def test_native_key_failure_releases_every_attempted_key(setup):
    desktop, _, pg, calls = setup

    def key_down(key, **kwargs):
        if key == 'a':
            raise RuntimeError('native input failed')
        calls.append(('down', key))

    pg.keyDown = key_down
    with pytest.raises(RuntimeError, match='native input failed'):
        desktop.call('hotkey', keys=['ctrl', 'a'])
    assert calls == [
        ('down', 'ctrl'), ('up', ('a',), {'_pause': False}),
        ('up', ('ctrl',), {'_pause': False}),
    ]
    assert pg.FAILSAFE is True


@pytest.mark.parametrize(('operation', 'args'), [
    ('move', {'x': -1, 'y': 100}),
    ('move', {'x': 1920, 'y': 100}),
    ('move', {'x': 10.5, 'y': 100}),
    ('move', {'x': True, 'y': 100}),
    ('move', {'x': 10, 'y': 1080}),
    ('move', {'x': 10, 'y': 100, 'duration': -1}),
    ('move', {'x': 10, 'y': 100, 'duration': 5.1}),
    ('move', {'x': 10, 'y': 100, 'duration': float('nan')}),
    ('drag', {'x': 10, 'y': 100, 'duration': float('inf')}),
    ('drag', {'x': 10, 'y': 100, 'button': 'unknown'}),
    ('click', {'x': 10, 'y': 100, 'clicks': 0}),
    ('click', {'x': 10, 'y': 100, 'clicks': 100}),
    ('click', {'x': 10, 'y': 100, 'clicks': True}),
    ('click', {'x': 10, 'y': 100, 'button': 'invalid'}),
    ('hotkey', {'keys': []}),
    ('hotkey', {'keys': 'ctrl+a'}),
    ('hotkey', {'keys': ['ctrl', 'unknown']}),
    ('hotkey', {'keys': ['ctrl', 'CTRL']}),
    ('hotkey', {'keys': ['ctrl', 'shift', 'win', 'f5', 'a', 'delete']}),
    ('key', {'key': 'unknown'}),
    ('key', {'key': None}),
    ('scroll', {'steps': 21}),
    ('scroll', {'steps': 1.5}),
    ('type', {'text': 'x' * 10_001}),
    ('type', {'text': None}),
])
def test_invalid_arguments_do_not_inject_actions(setup, operation, args):
    desktop, _, _, calls = setup
    with pytest.raises(ValueError):
        desktop.call(operation, **args)
    assert calls == []


@pytest.mark.parametrize('operation,args', [
    ('position', {}), ('screen_info', {}), ('screenshot', {}),
    ('click', {'x': 1, 'y': 1}), ('move', {'x': 1, 'y': 1}),
    ('drag', {'x': 1, 'y': 1}), ('hotkey', {'keys': ['ctrl', 'a']}),
    ('type', {'text': 'text'}), ('key', {'key': 'enter'}), ('scroll', {'steps': 1}),
])
def test_every_operation_requires_active_desktop_session(setup, operation, args):
    desktop, session, _, calls = setup
    session.stop()
    with pytest.raises(PermissionError):
        desktop.call(operation, **args)
    assert calls == []


def test_unicode_text_preserves_special_characters(setup, monkeypatch):
    desktop, session, _, calls = setup
    received = []
    monkeypatch.setattr('navix.unicode_input.type_unicode', lambda text, current: received.append((text, current)))
    desktop.call('type', text='Ação 😀\nsegunda linha')
    assert received == [('Ação 😀\nsegunda linha', session)]
    assert calls == []


def test_screenshot_returns_png_bytes(setup):
    desktop, _, pg, calls = setup

    def save(stream, format):
        assert isinstance(stream, io.BytesIO)
        assert format == 'PNG'
        stream.write(b'\x89PNG\r\n\x1a\nfixture')

    pg.screenshot = lambda: SimpleNamespace(save=save)
    assert desktop.call('screenshot').startswith(b'\x89PNG\r\n\x1a\n')
    assert calls == []

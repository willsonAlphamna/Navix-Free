"""Native desktop actions for the owner's currently authorized session."""
import math
import threading


def _integer(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f'{name} deve estar entre {minimum} e {maximum}.')
    return value


def _duration(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 5:
        raise ValueError('Duração deve estar entre 0 e 5 segundos.')
    return value


def _point(pg, x, y):
    width, height = pg.size()
    _integer(x, 'Coordenada x', 0, width - 1)
    _integer(y, 'Coordenada y', 0, height - 1)
    return x, y


def _button(value):
    if value not in {'left', 'middle', 'right'}:
        raise ValueError('Botão deve ser left, middle ou right.')
    return value


def _key(pg, value):
    if not isinstance(value, str) or not value or value.lower() not in pg.KEYBOARD_KEYS:
        raise ValueError('Tecla desconhecida.')
    return value.lower()


def _release_keys(pg, keys):
    # Releasing modifiers is cleanup, even after a corner fail-safe or revocation.
    # Never leave Ctrl/Shift/Win held down because the stop request interrupted a chord.
    previous = pg.FAILSAFE
    failure = None
    pg.FAILSAFE = False
    try:
        for key in reversed(keys):
            try:
                pg.keyUp(key, _pause=False)
            except Exception as error:
                failure = failure or error
    finally:
        pg.FAILSAFE = previous
    if failure:
        raise failure


class Desktop:
    def __init__(self, session):
        self.session = session
        self.lock = threading.RLock()

    def call(self, operation, **args):
        # Two clients must not interleave key chords or cursor movements.
        with self.lock:
            return self._call(operation, args)

    def _call(self, operation, args):
        self.session.require('desktop')
        import pyautogui as pg
        pg.FAILSAFE = True
        pg.PAUSE = .15
        if operation == 'position':
            x, y = pg.position()
            return {'x': x, 'y': y}
        if operation == 'screen_info':
            width, height = pg.size()
            x, y = pg.position()
            return {'width': width, 'height': height, 'x': x, 'y': y}
        if operation == 'screenshot':
            import io
            output = io.BytesIO()
            pg.screenshot().save(output, format='PNG')
            return output.getvalue()
        if operation == 'click':
            x, y = _point(pg, args['x'], args['y'])
            button = _button(args.get('button', 'left'))
            clicks = _integer(args.get('clicks', 1), 'Quantidade de cliques', 1, 3)
            pg.click(x, y, button=button, clicks=clicks, interval=.1 if clicks > 1 else 0)
        elif operation == 'move':
            x, y = _point(pg, args['x'], args['y'])
            pg.moveTo(x, y, duration=_duration(args.get('duration', .2)))
        elif operation == 'drag':
            x, y = _point(pg, args['x'], args['y'])
            duration = _duration(args.get('duration', .5))
            button = _button(args.get('button', 'left'))
            pg.dragTo(x, y, duration=duration, button=button)
        elif operation == 'type':
            text = args['text']
            if not isinstance(text, str) or len(text) > 10_000:
                raise ValueError('Informe texto com no máximo 10 mil caracteres.')
            # Windows Unicode input avoids replacing the user's clipboard.
            from .unicode_input import type_unicode
            type_unicode(text, self.session)
        elif operation == 'key':
            pg.press(_key(pg, args['key']))
        elif operation == 'hotkey':
            keys = args['keys']
            if not isinstance(keys, list) or not 1 <= len(keys) <= 5:
                raise ValueError('Informe de 1 a 5 teclas para o atalho.')
            checked = [_key(pg, key) for key in keys]
            if len(set(checked)) != len(checked):
                raise ValueError('O atalho não deve repetir a mesma tecla.')
            pressed = []
            try:
                for key in checked:
                    self.session.require('desktop')
                    pressed.append(key)
                    pg.keyDown(key, _pause=False)
            finally:
                _release_keys(pg, pressed)
        elif operation == 'scroll':
            pg.scroll(_integer(args['steps'], 'Rolagem', -20, 20))
        else:
            raise ValueError('Operação desconhecida.')
        return {'ok': True}

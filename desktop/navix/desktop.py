class Desktop:
    def __init__(self, session):
        self.session = session

    def call(self, operation, **args):
        self.session.require('desktop')
        import pyautogui as pg
        pg.FAILSAFE = True
        pg.PAUSE = .15
        if operation == 'screenshot':
            import io
            output = io.BytesIO()
            pg.screenshot().save(output, format='PNG')
            return output.getvalue()
        if operation == 'click':
            x, y = args['x'], args['y']
            width, height = pg.size()
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError('Coordenadas fora da tela.')
            pg.click(x, y)
        elif operation == 'type':
            text = args['text']
            if len(text) > 2000:
                raise ValueError('Máximo de 2000 caracteres.')
            # Windows Unicode input avoids replacing the user's clipboard.
            from .unicode_input import type_unicode
            type_unicode(text, self.session)
        elif operation == 'key':
            if args['key'] not in {'enter', 'tab', 'esc', 'backspace', 'up', 'down', 'left', 'right', 'space'}:
                raise ValueError('Tecla não permitida.')
            pg.press(args['key'])
        elif operation == 'scroll':
            pg.scroll(max(-20, min(20, args['steps'])))
        else:
            raise ValueError('Operação desconhecida.')
        return {'ok': True}

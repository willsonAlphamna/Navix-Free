"""Small bundled Python script runner; never opens the Navix panel as an interpreter."""
import os
from pathlib import Path
import runpy
import sys


def main(arguments=None):
    args = list(sys.argv[1:] if arguments is None else arguments)
    if getattr(sys, 'frozen', False):
        os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',
            str(Path(sys.executable).parent.parent / '_internal' / 'browsers'))
    if args and args[0] == '-u':
        args.pop(0)
    if args == ['--version'] or args == ['-V']:
        print('Navix Python ' + sys.version.split()[0])
        return 0
    if not args:
        raise ValueError('Informe -c código, -m módulo ou caminho de script Python.')
    sys.path.insert(0, os.getcwd())
    mode = args.pop(0)
    if mode == '-c':
        if not args:
            raise ValueError('Falta o código depois de -c.')
        code = args.pop(0)
        sys.argv = ['-c'] + args
        scope = {'__name__': '__main__', '__file__': '<navix-command>', '__package__': None}
        exec(compile(code, '<navix-command>', 'exec'), scope)
    elif mode == '-m':
        if not args:
            raise ValueError('Falta o nome do módulo depois de -m.')
        module = args.pop(0)
        sys.argv = [module] + args
        runpy.run_module(module, run_name='__main__', alter_sys=True)
    elif mode.startswith('-'):
        raise ValueError('Opção não suportada pelo executor. Use -c, -m ou arquivo.')
    else:
        script = Path(mode).resolve(strict=True)
        sys.argv = [str(script)] + args
        sys.path.insert(0, str(script.parent))
        runpy.run_path(str(script), run_name='__main__')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

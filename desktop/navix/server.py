import functools
import threading
import socket
from mcp.server.fastmcp import FastMCP, Image
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn
from .workspace import Workspace
from . import __version__


class TokenAuth:
    def __init__(self, app, session):
        self.app, self.session = app, session

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        value = headers.get(b'authorization', b'').decode('latin1')
        token = value[7:] if value.startswith('Bearer ') else ''
        if not self.session.authenticates(token):
            return await JSONResponse({'error': 'unauthorized'}, status_code=401)(scope, receive, send)
        await self.app(scope, receive, send)


def make_app(session, browser, desktop, port=8765):
    workspace = Workspace(session)
    mcp = FastMCP('Navix Desktop', host='127.0.0.1', port=port,
                  stateless_http=True, json_response=True)

    def audited(name, function):
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            try:
                result = function(*args, **kwargs)
                session.audit(name, 'ok')
                return result
            except Exception:
                session.audit(name, 'error')
                raise
        return wrapped

    def register(function):
        mcp.tool()(audited(function.__name__, function))
        return function

    @register
    def status() -> dict:
        """Estado real das permissões e tempo restante da sessão local."""
        return session.status()

    @register
    def browser_tabs() -> list:
        """Lista abas do navegador de automação aberto pelo proprietário."""
        return browser.call('tabs')

    @register
    def browser_open(url: str) -> dict:
        """Abre URL HTTP/HTTPS numa nova aba do perfil de automação."""
        return browser.call('open', url=url)

    @register
    def browser_read(page_id: str) -> str:
        """Lê até 30 mil caracteres visíveis da aba."""
        return browser.call('read', page_id=page_id)

    @register
    def browser_click(page_id: str, role: str, name: str) -> dict:
        """Clica um elemento pelo papel acessível e nome exato, sem ambiguidades."""
        return browser.call('click', page_id=page_id, role=role, name=name)

    @register
    def browser_fill(page_id: str, role: str, name: str, text: str) -> dict:
        """Preenche um campo identificado por papel e nome acessível exatos."""
        if len(text) > 10_000:
            raise ValueError('Texto excede 10 mil caracteres.')
        return browser.call('fill', page_id=page_id, role=role, name=name, text=text)

    @register
    def browser_scroll(page_id: str, pixels: int) -> dict:
        """Rola verticalmente uma aba, até 2000 pixels por chamada."""
        return browser.call('scroll', page_id=page_id, pixels=pixels)

    @register
    def browser_screenshot(page_id: str) -> Image:
        """Captura a área visível da aba autorizada."""
        return Image(data=browser.call('screenshot', page_id=page_id), format='png')

    @register
    def desktop_screenshot() -> Image:
        """Captura a tela inteira somente com permissão de desktop ativa."""
        return Image(data=desktop.call('screenshot'), format='png')

    @register
    def desktop_click(x: int, y: int, button: str = 'left', clicks: int = 1) -> dict:
        """Clica numa coordenada válida da tela; exige sessão autorizada."""
        return desktop.call('click', x=x, y=y, button=button, clicks=clicks)

    @register
    def desktop_type(text: str) -> dict:
        """Digita texto na janela em foco, com suporte a acentos no Windows."""
        return desktop.call('type', text=text)

    @register
    def desktop_key(key: str) -> dict:
        """Pressiona uma tecla reconhecida pelo teclado do Windows."""
        return desktop.call('key', key=key)

    @register
    def desktop_scroll(steps: int) -> dict:
        """Rola o mouse até 20 passos por chamada."""
        return desktop.call('scroll', steps=steps)

    @register
    def desktop_position() -> dict:
        """Retorna a posição atual do cursor do mouse."""
        return desktop.call('position')

    @register
    def desktop_screen_info() -> dict:
        """Dimensões da tela principal e posição do cursor."""
        return desktop.call('screen_info')

    @register
    def desktop_move(x: int, y: int, duration: float = .2) -> dict:
        """Move o cursor para uma coordenada da tela."""
        return desktop.call('move', x=x, y=y, duration=duration)

    @register
    def desktop_drag(x: int, y: int, duration: float = .5, button: str = 'left') -> dict:
        """Arrasta do cursor atual até uma coordenada da tela."""
        return desktop.call('drag', x=x, y=y, duration=duration, button=button)

    @register
    def desktop_hotkey(keys: list[str]) -> dict:
        """Executa combinação de teclas, por exemplo ['ctrl', 's'] ou ['alt', 'tab']."""
        return desktop.call('hotkey', keys=keys)

    @register
    def browser_start(kind: str = 'integrado') -> dict:
        """Abre o navegador integrado ou Opera com perfil separado autorizado."""
        return browser.call('start', kind=kind)

    @register
    def browser_navigate(page_id: str, url: str) -> dict:
        """Navega uma aba existente para uma URL HTTP/HTTPS."""
        return browser.call('navigate', page_id=page_id, url=url)

    @register
    def browser_close_tab(page_id: str) -> dict:
        """Fecha uma aba do perfil de automação."""
        return browser.call('close_tab', page_id=page_id)

    @register
    def browser_back(page_id: str) -> dict:
        """Volta à página anterior na aba."""
        return browser.call('back', page_id=page_id)

    @register
    def browser_forward(page_id: str) -> dict:
        """Avança no histórico da aba."""
        return browser.call('forward', page_id=page_id)

    @register
    def browser_reload(page_id: str) -> dict:
        """Recarrega a página e aguarda o DOM."""
        return browser.call('reload', page_id=page_id)

    @register
    def browser_snapshot(page_id: str) -> str:
        """Árvore acessível com nomes e funções dos elementos para localizar campos e botões."""
        return browser.call('snapshot', page_id=page_id)

    @register
    def browser_select(page_id: str, role: str, name: str, values: list[str]) -> dict:
        """Seleciona valores em uma lista HTML identificada por nome e função exatos."""
        return browser.call('select', page_id=page_id, role=role, name=name, values=values)

    @register
    def browser_press(page_id: str, role: str, name: str, key: str) -> dict:
        """Pressiona tecla ou atalho em um elemento identificado, por exemplo Enter."""
        return browser.call('press', page_id=page_id, role=role, name=name, key=key)

    @register
    def browser_hover(page_id: str, role: str, name: str) -> dict:
        """Posiciona o mouse sobre um elemento da página."""
        return browser.call('hover', page_id=page_id, role=role, name=name)

    @register
    def browser_wait(page_id: str, role: str, name: str, state: str = 'visible', timeout_ms: int = 10000) -> dict:
        """Aguarda estado de um elemento, até 30 segundos."""
        return browser.call('wait', page_id=page_id, role=role, name=name, state=state, timeout_ms=timeout_ms)

    @register
    def browser_upload(page_id: str, selector: str, paths: list[str]) -> dict:
        """Seleciona arquivos locais em input[type=file]; exige navegador e arquivos."""
        return browser.call('upload', page_id=page_id, selector=selector, paths=paths)

    @register
    def browser_download(page_id: str, role: str, name: str, destination: str, timeout_ms: int = 30000) -> dict:
        """Clica um link/botão de download e salva no caminho local explícito, sem sobrescrever."""
        return browser.call('download', page_id=page_id, role=role, name=name, destination=destination, timeout_ms=timeout_ms)

    @register
    def files_list(path: str, limit: int = 500) -> dict:
        """Lista arquivos e subpastas de um diretório local."""
        return workspace.call('list', path=path, limit=limit)

    @register
    def files_read(path: str, max_bytes: int = 1000000) -> dict:
        """Lê um arquivo UTF-8, indicando truncamento quando exceder o limite."""
        return workspace.call('read', path=path, max_bytes=max_bytes)

    @register
    def files_write(path: str, text: str, overwrite: bool = False) -> dict:
        """Cria arquivo UTF-8; substituir um existente exige overwrite=true."""
        return workspace.call('write', path=path, text=text, overwrite=overwrite)

    @register
    def files_edit(path: str, old_text: str, new_text: str, replace_all: bool = False) -> dict:
        """Substitui texto exato num arquivo. Recusa correspondência ambígua sem replace_all."""
        return workspace.call('edit', path=path, old_text=old_text, new_text=new_text, replace_all=replace_all)

    @register
    def files_mkdir(path: str, parents: bool = True) -> dict:
        """Cria uma pasta no caminho indicado."""
        return workspace.call('mkdir', path=path, parents=parents)

    @register
    def files_copy(source: str, destination: str, overwrite: bool = False) -> dict:
        """Copia arquivo ou pasta para um destino explícito."""
        return workspace.call('copy', source=source, destination=destination, overwrite=overwrite)

    @register
    def files_move(source: str, destination: str, overwrite: bool = False) -> dict:
        """Move ou renomeia arquivo/pasta; não sobrescreve por padrão."""
        return workspace.call('move', source=source, destination=destination, overwrite=overwrite)

    @register
    def files_delete(path: str, recursive: bool = False) -> dict:
        """Apaga permanentemente um arquivo ou pasta vazia. Árvore de pastas exige recursive=true."""
        return workspace.call('delete', path=path, recursive=recursive)

    @register
    def files_read_binary(path: str, max_bytes: int = 5000000) -> dict:
        """Retorna arquivo em base64 para transferir ao cliente MCP."""
        return workspace.call('read_binary', path=path, max_bytes=max_bytes)

    @register
    def files_write_binary(path: str, content_base64: str, overwrite: bool = False) -> dict:
        """Recebe conteúdo base64 do cliente MCP e grava arquivo binário local."""
        return workspace.call('write_binary', path=path, content_base64=content_base64, overwrite=overwrite)

    @register
    def files_download(url: str, destination: str, overwrite: bool = False,
                       max_bytes: int = 100000000, timeout_seconds: int = 30) -> dict:
        """Baixa HTTP/HTTPS para caminho local, com limite de tempo e tamanho."""
        return workspace.call('download', url=url, destination=destination, overwrite=overwrite,
                              max_bytes=max_bytes, timeout_seconds=timeout_seconds)

    @register
    def command_run(command: str, shell: str = 'powershell', cwd: str = '', timeout_seconds: int = 60) -> dict:
        """Executa PowerShell, cmd ou Python, retornando saída e código de término. Exige comandos."""
        return workspace.call('run', command=command, shell=shell, cwd=cwd, timeout_seconds=timeout_seconds)

    @register
    def command_exec(argv: list[str], cwd: str = '', timeout_seconds: int = 60) -> dict:
        """Executa programa por lista de argumentos, sem interpretação implícita por shell."""
        return workspace.call('exec', argv=argv, cwd=cwd, timeout_seconds=timeout_seconds)

    app = mcp.streamable_http_app()
    # Must wrap the app including its MCP lifecycle, not mount a second app.
    app.add_middleware(TokenAuth, session=session)
    async def health(request):
        return JSONResponse({'service': 'navix-desktop', 'version': __version__})
    app.routes.append(Route('/health', health))
    return app


class Service:
    def __init__(self, session, browser, desktop, port=8765):
        self.socket = None
        if port == 0:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('127.0.0.1', 0))
            port = self.socket.getsockname()[1]
        self.port = port
        self.app = make_app(session, browser, desktop, port)
        self.server = uvicorn.Server(uvicorn.Config(self.app, host='127.0.0.1', port=port,
                                    log_config=None, access_log=False))
        self.thread = None

    def start(self):
        if not self.thread:
            self.thread = threading.Thread(target=lambda: self.server.run(sockets=[self.socket] if self.socket else None), daemon=True, name='navix-mcp')
            self.thread.start()

    @property
    def ready(self):
        return bool(self.thread and self.thread.is_alive() and self.server.started and not self.server.should_exit)

    def close(self):
        self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=5)
        if self.socket:
            self.socket.close()

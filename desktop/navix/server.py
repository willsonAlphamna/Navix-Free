import functools
import threading
import socket
from mcp.server.fastmcp import FastMCP, Image
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn


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
    def desktop_click(x: int, y: int) -> dict:
        """Clica numa coordenada válida da tela; exige sessão autorizada."""
        return desktop.call('click', x=x, y=y)

    @register
    def desktop_type(text: str) -> dict:
        """Digita texto na janela em foco, com suporte a acentos no Windows."""
        return desktop.call('type', text=text)

    @register
    def desktop_key(key: str) -> dict:
        """Pressiona tecla simples permitida; não executa atalhos de sistema."""
        return desktop.call('key', key=key)

    @register
    def desktop_scroll(steps: int) -> dict:
        """Rola o mouse até 20 passos por chamada."""
        return desktop.call('scroll', steps=steps)

    app = mcp.streamable_http_app()
    # Must wrap the app including its MCP lifecycle, not mount a second app.
    app.add_middleware(TokenAuth, session=session)
    async def health(request):
        return JSONResponse({'service': 'navix-desktop', 'version': '0.1.0'})
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

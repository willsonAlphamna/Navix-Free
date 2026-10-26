"""Playwright runs on one dedicated thread; pages are addressed by stable IDs."""
import os
import shutil
import tempfile
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
import time


def validate_url(url):
    if not isinstance(url, str) or len(url) > 16_384:
        raise ValueError('URL inválida ou muito longa.')
    parsed = urlsplit(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Use uma URL http ou https sem credenciais.')
    return url


def operation_timeout(value, default=10_000, maximum=30_000):
    value = default if value is None else value
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ValueError('Prazo inválido para a operação do navegador.')
    return value


def upload_paths(paths):
    if not isinstance(paths, list) or not paths or len(paths) > 100:
        raise ValueError('Informe de 1 a 100 arquivos para enviar.')
    result = []
    for value in paths:
        if not isinstance(value, str) or not value:
            raise ValueError('Caminho de arquivo inválido.')
        path = Path(value).expanduser().resolve(strict=True)
        if not path.is_file():
            raise ValueError('O envio exige arquivos existentes, não pastas.')
        result.append(str(path))
    return result


class Browser:
    def __init__(self, session, headless=False):
        self.session = session
        self.headless = headless
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='navix-browser')
        self.pw = self.context = self.process = None
        self.pages = {}
        self.counter = 0

    def call(self, operation, **kwargs):
        return self.worker.submit(self._call, operation, kwargs).result(timeout=65)

    def _start(self, kind):
        if kind not in {'integrado', 'opera'}:
            raise ValueError('Navegador deve ser integrado ou opera.')
        if self.context:
            return
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        profile = self.session.directory / ('browser-' + kind)
        try:
            if kind == 'opera':
                roots = [Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Opera',
                         Path(os.environ.get('PROGRAMFILES', '')) / 'Opera']
                exe = next((p / name for p in roots for name in ('launcher.exe', 'opera.exe')
                            if (p / name).is_file()), None)
                if exe is None:
                    raise RuntimeError('Opera não encontrado. Escolha o navegador integrado.')
                # Dedicated port and profile; existing Opera windows remain independent.
                self.process = subprocess.Popen([str(exe), '--remote-debugging-address=127.0.0.1',
                    '--remote-debugging-port=9223', '--user-data-dir=' + str(profile), 'about:blank'])
                for attempt in range(15):
                    try:
                        browser = self.pw.chromium.connect_over_cdp('http://127.0.0.1:9223', timeout=1000)
                        self.context = browser.contexts[0]
                        break
                    except Exception:
                        time.sleep(.3)
                if not self.context:
                    raise RuntimeError('Opera não respondeu na porta 9223.')
            else:
                self.context = self.pw.chromium.launch_persistent_context(str(profile), headless=self.headless,
                    accept_downloads=True, viewport={'width': 1100, 'height': 760})
            self.context.set_default_timeout(10_000)
            self.context.set_default_navigation_timeout(20_000)
        except Exception:
            self._close()
            raise

    def _page(self, page_id):
        page = self.pages.get(page_id)
        if page is None or page.is_closed():
            raise ValueError('Aba inexistente. Liste as abas novamente.')
        return page

    def _locator(self, page, role, name):
        locator = page.get_by_role(role, name=name, exact=True)
        if locator.count() != 1:
            raise ValueError('Elemento ausente ou ambíguo; use nome e função exatos.')
        return locator

    def _download(self, page, args):
        self.session.require('files')
        raw = args['destination']
        if not isinstance(raw, str) or not raw:
            raise ValueError('Informe o caminho completo do arquivo de destino.')
        target = Path(raw).expanduser().resolve()
        if target.exists():
            raise FileExistsError('O arquivo de destino já existe.')
        if not target.parent.is_dir():
            raise ValueError('A pasta de destino não existe.')
        timeout = operation_timeout(args.get('timeout_ms'), 30_000, 45_000)
        locator = self._locator(page, args['role'], args['name'])
        temporary = Path(tempfile.mkdtemp(prefix='.navix-download-', dir=target.parent))
        # CDP provides completion events and cancellation without blocking in
        # Download.save_as(), which has no transfer timeout. All protocol calls
        # and event pumping stay on this browser's dedicated Playwright thread.
        control = None
        target_control = None
        frame_ids = set()
        def visit(tree):
            frame_ids.add(tree['frame']['id'])
            for child in tree.get('childFrames', []):
                visit(child)
        transfer = {}
        def begun(event):
            if event.get('frameId') in frame_ids and not transfer:
                transfer.update(event)
                transfer['state'] = 'inProgress'
        def progress(event):
            if transfer.get('guid') == event.get('guid'):
                transfer.update(event)
        created = False
        completed = False
        try:
            control = self.context.browser.new_browser_cdp_session()
            target_control = self.context.new_cdp_session(page)
            visit(target_control.send('Page.getFrameTree')['frameTree'])
            control.on('Browser.downloadWillBegin', begun)
            control.on('Browser.downloadProgress', progress)
            control.send('Browser.setDownloadBehavior', {'behavior': 'allowAndName',
                         'downloadPath': str(temporary), 'eventsEnabled': True})
            deadline = time.monotonic() + timeout / 1000
            # A download may look like a navigation until the response headers
            # arrive. Observe it through CDP instead of waiting inside click.
            locator.click(timeout=min(timeout, 10_000), no_wait_after=True)
            while transfer.get('state') != 'completed':
                self.session.require('browser')
                self.session.require('files')
                if transfer.get('state') == 'canceled':
                    raise RuntimeError('O download foi cancelado pelo navegador.')
                if time.monotonic() >= deadline:
                    raise TimeoutError('Prazo de início ou transferência do download excedido.')
                page.wait_for_timeout(100)
            self.session.require('browser')
            self.session.require('files')
            # The GUID is generated by Chromium, never by a remote filename.
            staged = temporary / transfer['guid']
            with staged.open('rb') as source, target.open('xb') as output:
                created = True
                while chunk := source.read(1024 * 1024):
                    self.session.require('browser')
                    self.session.require('files')
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Prazo de transferência do download excedido.')
                    output.write(chunk)
            self.session.require('browser')
            self.session.require('files')
            completed = True
            return {'ok': True, 'path': str(target), 'bytes': target.stat().st_size,
                    'suggested_filename': transfer.get('suggestedFilename', '')}
        finally:
            if transfer.get('guid') and transfer.get('state') != 'completed':
                try:
                    control.send('Browser.cancelDownload', {'guid': transfer['guid']})
                except Exception:
                    pass
            if not completed and target_control:
                # A server can delay even the response headers, before Chromium
                # has assigned a download GUID. Abort that pending navigation.
                try:
                    target_control.send('Page.stopLoading')
                except Exception:
                    pass
            if target_control:
                try:
                    target_control.detach()
                except Exception:
                    pass
            try:
                control.send('Browser.setDownloadBehavior', {'behavior': 'default', 'eventsEnabled': False})
            except Exception:
                pass
            try:
                control.detach()
            except Exception:
                pass
            shutil.rmtree(temporary, ignore_errors=True)
            if created and not completed:
                target.unlink(missing_ok=True)

    def _call(self, operation, args):
        self.session.require('browser')
        if operation == 'start':
            self._start(args.get('kind', 'integrado'))
            return {'ok': True}
        if not self.context:
            raise RuntimeError('Abra o navegador pelo painel primeiro.')
        if operation == 'tabs':
            for page in self.context.pages:
                if page not in self.pages.values():
                    self.counter += 1
                    self.pages[str(self.counter)] = page
            return [{'id': key, 'url': page.url, 'title': page.title()}
                    for key, page in self.pages.items() if not page.is_closed()]
        if operation == 'open':
            url = validate_url(args['url'])
            page = self.context.new_page()
            self.counter += 1
            self.pages[str(self.counter)] = page
            page.goto(url, wait_until='domcontentloaded')
            return {'id': str(self.counter), 'url': page.url}
        page = self._page(args['page_id'])
        if operation == 'navigate':
            page.goto(validate_url(args['url']), wait_until='domcontentloaded')
            return {'ok': True, 'id': args['page_id'], 'url': page.url}
        if operation == 'close_tab':
            page.close()
            self.pages.pop(args['page_id'], None)
            return {'ok': True}
        if operation in {'back', 'forward', 'reload'}:
            methods = {'back': page.go_back, 'forward': page.go_forward, 'reload': page.reload}
            methods[operation](wait_until='domcontentloaded')
            return {'ok': True, 'url': page.url}
        if operation == 'read':
            return page.locator('body').inner_text()[:30_000]
        if operation == 'snapshot':
            return page.locator('body').aria_snapshot()[:30_000]
        if operation == 'wait':
            state = args.get('state', 'visible')
            if state not in {'attached', 'detached', 'visible', 'hidden'}:
                raise ValueError('Estado deve ser attached, detached, visible ou hidden.')
            locator = page.get_by_role(args['role'], name=args['name'], exact=True)
            if locator.count() > 1:
                raise ValueError('Elemento ambíguo; use nome e função exatos.')
            locator.wait_for(state=state, timeout=operation_timeout(args.get('timeout_ms')))
            self.session.require('browser')
            return {'ok': True, 'state': state}
        if operation in {'click', 'fill', 'hover', 'press', 'select'}:
            locator = self._locator(page, args['role'], args['name'])
            if operation == 'click':
                locator.click()
            elif operation == 'fill':
                locator.fill(args['text'])
            elif operation == 'hover':
                locator.hover()
            elif operation == 'press':
                key = args['key']
                if not isinstance(key, str) or not 1 <= len(key) <= 100:
                    raise ValueError('Tecla ou atalho inválido.')
                locator.press(key)
            elif operation == 'select':
                values = args['values']
                if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
                    raise ValueError('Informe uma lista de valores de opções.')
                selected = locator.select_option(value=values)
                return {'ok': True, 'values': selected}
            return {'ok': True}
        if operation == 'upload':
            self.session.require('files')
            paths = upload_paths(args['paths'])
            selector = args['selector']
            if not isinstance(selector, str) or not selector:
                raise ValueError('Informe o seletor do campo de arquivo.')
            locator = page.locator(selector)
            if locator.count() != 1:
                raise ValueError('Campo de arquivo ausente ou ambíguo.')
            self.session.require('browser')
            self.session.require('files')
            locator.set_input_files(paths)
            return {'ok': True, 'files': [Path(path).name for path in paths]}
        if operation == 'download':
            return self._download(page, args)
        if operation == 'scroll':
            page.mouse.wheel(0, max(-2000, min(2000, args['pixels'])))
            return {'ok': True}
        if operation == 'screenshot':
            return page.screenshot(type='png')
        raise ValueError('Operação desconhecida.')

    def _close(self):
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
        if self.pw:
            self.pw.stop()
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.context = self.pw = self.process = None
        self.pages.clear()

    def close(self):
        self.worker.submit(self._close).result(timeout=15)

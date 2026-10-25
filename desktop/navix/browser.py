"""Playwright runs on one dedicated thread; pages are addressed by stable IDs."""
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
import time


def validate_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Use uma URL http ou https sem credenciais.')
    return url


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
                    accept_downloads=False, viewport={'width': 1100, 'height': 760})
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
        if operation == 'read':
            return page.locator('body').inner_text()[:30_000]
        if operation in {'click', 'fill'}:
            locator = page.get_by_role(args['role'], name=args['name'], exact=True)
            if locator.count() != 1:
                raise ValueError('Elemento ausente ou ambíguo; use nome e função exatos.')
            if operation == 'click':
                locator.click()
            else:
                locator.fill(args['text'])
            return {'ok': True}
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

    def close(self):
        self.worker.submit(self._close).result(timeout=15)

"""Real browser transfers, navigation, and permission boundaries."""
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from navix.browser import Browser, operation_timeout, upload_paths, validate_url
from navix.core import Session


@pytest.mark.parametrize('url', ['file:///tmp/a', 'javascript:alert(1)',
                                 'https://name:password@example.org', 5, 'x' * 16_385])
def test_reject_invalid_navigation(url):
    with pytest.raises(ValueError):
        validate_url(url)


@pytest.mark.parametrize('value', [0, -1, True, 30_001, '100', 1.5])
def test_invalid_timeout(value):
    with pytest.raises(ValueError):
        operation_timeout(value)


def test_upload_paths_require_existing_files(tmp_path):
    data = tmp_path / 'data.txt'
    data.write_text('Navix', encoding='utf-8')
    assert upload_paths([str(data)]) == [str(data.resolve())]
    for paths in ([], [str(tmp_path)], [''], 'data.txt'):
        with pytest.raises(ValueError):
            upload_paths(paths)
    with pytest.raises(FileNotFoundError):
        upload_paths([str(tmp_path / 'missing')])


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/download'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', 'attachment; filename="from-server.txt"')
            self.send_header('Content-Length', '14')
            self.end_headers()
            try:
                self.wfile.write(b'Navix ')
                self.wfile.flush()
                if self.path == '/download-slow':
                    time.sleep(3)
                self.wfile.write(b'Download')
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        title = 'Second' if self.path == '/second' else 'First'
        content = f'''<html><head><title>{title}</title></head><body>
        <a href="/second">Próxima</a>
        <label>Nome<input id="name"></label>
        <label for="color">Cor</label><select id="color" onchange="document.querySelector('#result').textContent=this.value">
        <option value="red">Vermelho</option><option value="blue">Azul</option></select>
        <label>Arquivo<input type="file" id="file" onchange="document.querySelector('#result').textContent=this.files[0].name"></label>
        <p id="result"></p><a href="/download">Baixar</a><a href="/download-slow">Baixar lento</a>
        <button onclick="document.querySelector('#result').textContent=document.querySelector('#name').value">Confirmar</button>
        </body></html>'''.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args):
        pass


@pytest.fixture
def real_browser(tmp_path):
    if os.environ.get('NAVIX_TEST_BROWSER') != '1':
        pytest.skip('Requires installed Chromium')
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    session = Session(tmp_path / 'state')
    session.activate(['browser', 'files'])
    browser = Browser(session, headless=True)
    try:
        browser.call('start')
        yield browser, session, 'http://127.0.0.1:%s' % server.server_port
    finally:
        browser.close()
        browser.worker.shutdown(wait=True)
        server.shutdown()
        server.server_close()


def test_real_navigation_form_upload_download(real_browser, tmp_path):
    browser, session, url = real_browser
    page = browser.call('open', url=url)['id']
    snapshot = browser.call('snapshot', page_id=page)
    assert 'textbox "Nome"' in snapshot
    browser.call('hover', page_id=page, role='link', name='Próxima')
    browser.call('wait', page_id=page, role='textbox', name='Nome')
    browser.call('fill', page_id=page, role='textbox', name='Nome', text='Willson')
    browser.call('press', page_id=page, role='textbox', name='Nome', key='End')
    browser.call('click', page_id=page, role='button', name='Confirmar')
    assert 'Willson' in browser.call('read', page_id=page)
    browser.call('select', page_id=page, role='combobox', name='Cor', values=['blue'])
    assert 'blue' in browser.call('read', page_id=page)
    local = tmp_path / 'local.txt'
    local.write_text('Upload verificado', encoding='utf-8')
    browser.call('upload', page_id=page, selector='#file', paths=[str(local)])
    assert 'local.txt' in browser.call('read', page_id=page)
    target = tmp_path / 'saved.txt'
    result = browser.call('download', page_id=page, role='link', name='Baixar', destination=str(target))
    assert result['bytes'] == 14
    assert target.read_bytes() == b'Navix Download'
    with pytest.raises(FileExistsError):
        browser.call('download', page_id=page, role='link', name='Baixar', destination=str(target))
    assert target.read_bytes() == b'Navix Download'
    browser.call('navigate', page_id=page, url=url + '/second')
    assert browser.call('back', page_id=page)['url'] == url + '/'
    assert browser.call('forward', page_id=page)['url'] == url + '/second'
    assert browser.call('reload', page_id=page)['url'] == url + '/second'
    with session.lock:
        session.permissions.remove('files')
    with pytest.raises(PermissionError):
        browser.call('upload', page_id=page, selector='#file', paths=[str(local)])
    with pytest.raises(PermissionError):
        browser.call('download', page_id=page, role='link', name='Baixar', destination=str(tmp_path / 'denied'))
    browser.call('close_tab', page_id=page)
    assert all(tab['id'] != page for tab in browser.call('tabs'))


def test_real_download_transfer_deadline(real_browser, tmp_path):
    browser, session, url = real_browser
    page = browser.call('open', url=url)['id']
    target = tmp_path / 'timeout.txt'
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        browser.call('download', page_id=page, role='link', name='Baixar lento',
                     destination=str(target), timeout_ms=500)
    assert time.monotonic() - started < 2.5
    assert not target.exists()
    assert not list(tmp_path.glob('.navix-download-*'))


def test_real_download_revoked_during_transfer(real_browser, tmp_path):
    browser, session, url = real_browser
    page = browser.call('open', url=url)['id']
    target = tmp_path / 'revoked.txt'
    timer = threading.Timer(.5, session.stop)
    timer.start()
    try:
        with pytest.raises(PermissionError):
            browser.call('download', page_id=page, role='link', name='Baixar lento',
                         destination=str(target), timeout_ms=5000)
    finally:
        timer.cancel()
    assert not target.exists()
    assert not list(tmp_path.glob('.navix-download-*'))

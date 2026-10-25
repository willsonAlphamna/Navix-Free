import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from navix.browser import Browser
from navix.core import Session


@pytest.mark.skipif(os.environ.get('NAVIX_TEST_BROWSER') != '1', reason='Requires installed Chromium')
def test_real_browser_flow(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            content = b'''<html><head><title>Navix Test</title></head><body>
            <label for="name">Nome</label><input id="name">
            <button onclick="document.querySelector('#result').textContent='OK '+document.querySelector('input').value">Testar</button>
            <p id="result"></p><div style="height:3000px">Fim</div></body></html>'''
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
        def log_message(self, *args): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    session = Session(tmp_path)
    session.activate(['browser'])
    browser = Browser(session, headless=True)
    try:
        browser.call('start')
        page = browser.call('open', url='http://127.0.0.1:%s' % server.server_port)['id']
        assert any(tab['title'] == 'Navix Test' for tab in browser.call('tabs'))
        browser.call('fill', page_id=page, role='textbox', name='Nome', text='Wilson')
        browser.call('click', page_id=page, role='button', name='Testar')
        assert 'OK Wilson' in browser.call('read', page_id=page)
        browser.call('scroll', page_id=page, pixels=700)
        assert browser.call('screenshot', page_id=page).startswith(b'\x89PNG')
        session.stop()
        with pytest.raises(PermissionError): browser.call('read', page_id=page)
    finally:
        browser.close()
        browser.worker.shutdown(wait=True)
        server.shutdown()
        server.server_close()

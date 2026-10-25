"""End-to-end validation of the packaged app on the Windows build runner."""
import json
from pathlib import Path
import tempfile
import threading
import time
import traceback
from urllib.request import Request, urlopen
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .browser import Browser
from .core import Session
from .desktop import Desktop
from .server import Service


def run(report_path):
    report = {'ok': False, 'checks': []}
    browser = service = fixture = root = None
    try:
        import tkinter as tk
        root = tk.Tk()
        root.title('Navix — teste automatizado')
        root.geometry('500x250+100+100')
        field = tk.Entry(root, name='unicode_test')
        field.pack(padx=20, pady=20)
        root.update()
        report['checks'].append('tk_window')
        with tempfile.TemporaryDirectory(prefix='navix-selftest-') as directory:
            session = Session(Path(directory))
            browser = Browser(session)
            service = Service(session, browser, Desktop(session), port=18765)
            service.start()
            for _ in range(100):
                if service.server.started: break
                time.sleep(.1)
            if not service.server.started: raise RuntimeError('Servidor não iniciou')
            token = session.token
            def rpc(name, arguments):
                payload = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                                      'params': {'name': name, 'arguments': arguments}}).encode()
                req = Request('http://127.0.0.1:18765/mcp', data=payload, headers={
                    'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                    'Accept': 'application/json, text/event-stream',
                    'MCP-Protocol-Version': '2025-03-26'})
                with urlopen(req, timeout=45) as response:
                    result = json.load(response)['result']
                if result.get('isError'): raise RuntimeError(str(result))
                return result
            assert 'false' in json.dumps(rpc('status', {})).lower()
            report['checks'].append('packaged_mcp_status')
            session.activate(['browser', 'desktop'])
            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(b'<label for="n">Nome</label><input id="n"><button onclick="document.body.dataset.ok=1;document.querySelector(\'p\').textContent=\'SUCESSO\'">Testar</button><p></p>')
                def log_message(self, *args): pass
            fixture = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            threading.Thread(target=fixture.serve_forever, daemon=True).start()
            browser.call('start')
            result = rpc('browser_open', {'url': 'http://127.0.0.1:%d' % fixture.server_port})
            page_id = json.loads(result['content'][0]['text'])['id']
            rpc('browser_fill', {'page_id': page_id, 'role': 'textbox', 'name': 'Nome', 'text': 'Navix'})
            rpc('browser_click', {'page_id': page_id, 'role': 'button', 'name': 'Testar'})
            assert 'SUCESSO' in json.dumps(rpc('browser_read', {'page_id': page_id}))
            assert any(item['type'] == 'image' for item in rpc('browser_screenshot', {'page_id': page_id})['content'])
            report['checks'].append('packaged_browser_mcp_full_flow')
            assert any(item['type'] == 'image' for item in rpc('desktop_screenshot', {})['content'])
            report['checks'].append('packaged_desktop_screenshot')
            # Focus only our test window, never an unrelated application.
            root.lift()
            root.attributes('-topmost', True)
            field.focus_force()
            root.update()
            rpc('desktop_type', {'text': 'a\u00e7\u00e3o'})
            root.update()
            assert field.get() == 'a\u00e7\u00e3o', repr(field.get())
            report['checks'].append('packaged_unicode_input')
            session.stop()
            from urllib.error import HTTPError
            try:
                rpc('status', {})
                raise AssertionError('Credencial revogada ainda aceita')
            except HTTPError as error:
                assert error.code == 401
            report['checks'].append('packaged_revocation')
            browser.close()
            browser.worker.shutdown(wait=True)
            browser = None
            service.close()
            service = None
        report['ok'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if browser:
            try: browser.close()
            except Exception: pass
            browser.worker.shutdown(wait=False, cancel_futures=True)
        if service: service.close()
        if fixture:
            fixture.shutdown()
            fixture.server_close()
        if root: root.destroy()
        Path(report_path).write_text(json.dumps(report, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1

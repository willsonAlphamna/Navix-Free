"""End-to-end validation of the packaged app on the Windows build runner."""
import base64
import json
from pathlib import Path
import sys
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
    browser = service = fixture = root = session = None
    original_position = None
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
            service = Service(session, browser, Desktop(session), port=0)
            service.start()
            for _ in range(100):
                if service.server.started: break
                time.sleep(.1)
            if not service.server.started: raise RuntimeError('Servidor não iniciou')
            token = session.token
            def rpc(name, arguments):
                payload = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                                      'params': {'name': name, 'arguments': arguments}}).encode()
                req = Request('http://127.0.0.1:%d/mcp' % service.port, data=payload, headers={
                    'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                    'Accept': 'application/json, text/event-stream',
                    'MCP-Protocol-Version': '2025-03-26'})
                with urlopen(req, timeout=45) as response:
                    result = json.load(response)['result']
                if result.get('isError'): raise RuntimeError(str(result))
                return result

            def tool_data(name, arguments):
                result = rpc(name, arguments)
                if 'structuredContent' in result:
                    return result['structuredContent']
                for item in result.get('content', []):
                    if item.get('type') == 'text':
                        return json.loads(item['text'])
                raise AssertionError('Ferramenta não retornou dados: ' + name)

            assert 'false' in json.dumps(rpc('status', {})).lower()
            report['checks'].append('packaged_mcp_status')
            session.activate(['browser', 'desktop', 'files', 'commands'])
            download_content = b'NAVIX_LOCAL_DOWNLOAD_OK\n'
            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/download':
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Content-Disposition', 'attachment; filename="navix-fixture.txt"')
                        self.send_header('Content-Length', str(len(download_content)))
                        self.end_headers()
                        self.wfile.write(download_content)
                        return
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(b'''<!doctype html><html lang="pt-BR"><body>
                        <label for="n">Nome</label><input id="n">
                        <button onclick="document.getElementById('result').textContent='SUCESSO'">Testar</button>
                        <p id="result"></p>
                        <label for="upload">Enviar arquivo</label>
                        <input id="upload" type="file" onchange="this.files[0].text().then(t=>document.getElementById('uploaded').textContent=t)">
                        <p id="uploaded"></p><a href="/download" download>Baixar arquivo</a>
                        </body></html>''')
                def log_message(self, *args): pass
            fixture = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            threading.Thread(target=fixture.serve_forever, daemon=True).start()
            browser.call('start')
            fixture_url = 'http://127.0.0.1:%d' % fixture.server_port
            page_id = tool_data('browser_open', {'url': fixture_url})['id']
            rpc('browser_fill', {'page_id': page_id, 'role': 'textbox', 'name': 'Nome', 'text': 'Navix'})
            rpc('browser_click', {'page_id': page_id, 'role': 'button', 'name': 'Testar'})
            assert 'SUCESSO' in json.dumps(rpc('browser_read', {'page_id': page_id}))
            assert any(item['type'] == 'image' for item in rpc('browser_screenshot', {'page_id': page_id})['content'])
            report['checks'].append('packaged_browser_mcp_full_flow')

            # Exercise actual files through MCP, entirely in the temporary fixture.
            files_directory = Path(directory) / 'files-test'
            rpc('files_mkdir', {'path': str(files_directory)})
            source = files_directory / 'source.txt'
            original_text = 'NAVIX_UPLOAD_ORIGINAL ação'
            edited_text = 'NAVIX_UPLOAD_EDITED ação'
            rpc('files_write', {'path': str(source), 'text': original_text})
            assert tool_data('files_read', {'path': str(source)})['content'] == original_text
            rpc('files_edit', {'path': str(source), 'old_text': 'ORIGINAL', 'new_text': 'EDITED'})
            assert tool_data('files_read', {'path': str(source)})['content'] == edited_text
            copied = files_directory / 'copy.txt'
            moved = files_directory / 'moved.txt'
            rpc('files_copy', {'source': str(source), 'destination': str(copied)})
            rpc('files_move', {'source': str(copied), 'destination': str(moved)})
            assert not copied.exists()
            assert tool_data('files_read', {'path': str(moved)})['content'] == edited_text
            listing = tool_data('files_list', {'path': str(files_directory)})
            assert {entry['name'] for entry in listing['entries']} == {'source.txt', 'moved.txt'}
            binary_path = files_directory / 'binary.bin'
            binary = b'\x00\xffNAVIX_BINARY\r\n'
            rpc('files_write_binary', {'path': str(binary_path),
                                      'content_base64': base64.b64encode(binary).decode('ascii')})
            received = tool_data('files_read_binary', {'path': str(binary_path)})
            assert base64.b64decode(received['content_base64'], validate=True) == binary
            report['checks'].append('packaged_files_write_read_edit_list_copy_move_binary')

            # Browser upload is verified by the page reading the actual local file.
            rpc('browser_upload', {'page_id': page_id, 'selector': '#upload', 'paths': [str(source)]})
            for _ in range(30):
                if edited_text in json.dumps(rpc('browser_read', {'page_id': page_id}), ensure_ascii=False):
                    break
                time.sleep(.1)
            else:
                raise AssertionError('Página não recebeu o conteúdo do upload')
            browser_download = files_directory / 'browser-download.txt'
            rpc('browser_download', {'page_id': page_id, 'role': 'link', 'name': 'Baixar arquivo',
                                     'destination': str(browser_download)})
            assert browser_download.read_bytes() == download_content
            direct_download = files_directory / 'direct-download.txt'
            rpc('files_download', {'url': fixture_url + '/download', 'destination': str(direct_download)})
            assert direct_download.read_bytes() == download_content
            report['checks'].append('packaged_browser_upload_download_and_http_download')

            python_result = tool_data('command_run', {'shell': 'python', 'command':
                "import sys, json, playwright, pyautogui, PIL; "
                "print(json.dumps({'marker': 'NAVIX_PYTHON_IMPORTS_OK', 'executable': sys.executable}))"})
            assert python_result['exit_code'] == 0, python_result
            assert not python_result['timed_out'] and not python_result['output_truncated']
            python_info = json.loads(python_result['stdout'].strip())
            assert python_info['marker'] == 'NAVIX_PYTHON_IMPORTS_OK'
            if getattr(sys, 'frozen', False):
                expected_python = Path(sys.executable).parent / 'python-runtime' / 'NavixPython.exe'
                assert Path(python_info['executable']).resolve() == expected_python.resolve(), python_info
            report['checks'].append('packaged_python_runtime_and_imports')
            powershell = tool_data('command_run', {'shell': 'powershell',
                                                   'command': "Write-Output 'NAVIX_POWERSHELL_OK'"})
            assert powershell['exit_code'] == 0 and 'NAVIX_POWERSHELL_OK' in powershell['stdout'], powershell
            executed = tool_data('command_exec', {'argv': [python_info['executable'], '-c',
                                                          "print('NAVIX_DIRECT_EXEC_OK')"]})
            assert executed['exit_code'] == 0 and 'NAVIX_DIRECT_EXEC_OK' in executed['stdout'], executed
            report['checks'].append('packaged_powershell_and_direct_command')

            # Overwrite and recursive delete are tested only on disposable fixture paths.
            replace_target = files_directory / 'overwrite.txt'
            rpc('files_write', {'path': str(replace_target), 'text': 'ANTES'})
            try:
                rpc('files_write', {'path': str(replace_target), 'text': 'DEPOIS'})
                raise AssertionError('Sobrescrita sem autorização foi aceita')
            except RuntimeError:
                pass
            rpc('files_write', {'path': str(replace_target), 'text': 'DEPOIS', 'overwrite': True})
            assert replace_target.read_text(encoding='utf-8') == 'DEPOIS'
            nested = files_directory / 'pasta' / 'subpasta'
            rpc('files_mkdir', {'path': str(nested)})
            rpc('files_write', {'path': str(nested / 'arquivo.txt'), 'text': 'APAGAR_TESTE'})
            try:
                rpc('files_delete', {'path': str(nested.parent)})
                raise AssertionError('Remoção recursiva implícita foi aceita')
            except RuntimeError:
                pass
            rpc('files_delete', {'path': str(nested.parent), 'recursive': True})
            assert not nested.parent.exists()
            rpc('files_delete', {'path': str(replace_target)})
            report['checks'].append('packaged_files_overwrite_and_recursive_delete')

            # Delete only files just created in our own fixture directory.
            for created in (source, moved, binary_path, browser_download, direct_download):
                rpc('files_delete', {'path': str(created)})
                assert not created.exists()
            rpc('files_delete', {'path': str(files_directory)})
            assert not files_directory.exists()
            report['checks'].append('packaged_files_delete')

            assert any(item['type'] == 'image' for item in rpc('desktop_screenshot', {})['content'])
            report['checks'].append('packaged_desktop_screenshot')
            screen_info = tool_data('desktop_screen_info', {})
            assert screen_info['width'] > 0 and screen_info['height'] > 0
            original_position = tool_data('desktop_position', {})
            # Focus only our test window, never an unrelated application.
            root.lift()
            root.attributes('-topmost', True)
            field.insert(0, 'SUBSTITUIR')
            field.focus_force()
            root.update()
            x = field.winfo_rootx() + field.winfo_width() // 2
            y = field.winfo_rooty() + field.winfo_height() // 2
            assert 0 <= x < screen_info['width'] and 0 <= y < screen_info['height']
            # Build runners may leave the cursor at (0, 0), a PyAutoGUI fail-safe
            # corner. Set up our fixture inside its own window without disabling
            # the fail-safe, then test the real MCP movement from that position.
            import ctypes
            if not ctypes.windll.user32.SetCursorPos(x + 5, y + 5):
                raise RuntimeError('Windows não preparou o cursor para o autoteste')
            rpc('desktop_move', {'x': x, 'y': y, 'duration': .2})
            assert tool_data('desktop_position', {}) == {'x': x, 'y': y}
            rpc('desktop_click', {'x': x, 'y': y})
            root.update()
            assert root.focus_get() == field
            rpc('desktop_hotkey', {'keys': ['ctrl', 'a']})
            root.update()
            rpc('desktop_type', {'text': 'a\u00e7\u00e3o'})
            root.update()
            assert field.get() == 'a\u00e7\u00e3o', repr(field.get())
            report['checks'].append('packaged_mouse_move_click_hotkey_unicode_input')
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
        if original_position is not None:
            # Cleanup remains necessary if an assertion fails mid-mouse test.
            try:
                import ctypes
                if not ctypes.windll.user32.SetCursorPos(original_position['x'], original_position['y']):
                    raise RuntimeError('Windows não restaurou a posição do cursor')
            except Exception:
                report['ok'] = False
                report['cursor_restore_error'] = traceback.format_exc()
        if session and session.directory.exists():
            try:
                session.stop()
            except Exception:
                report['ok'] = False
                report['session_cleanup_error'] = traceback.format_exc()
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

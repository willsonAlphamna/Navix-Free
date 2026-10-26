import base64
import errno
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import sys
import threading
import time

import pytest

from navix.core import Session
from navix.workspace import Workspace


@pytest.fixture
def workspace(tmp_path):
    session = Session(tmp_path / 'session')
    session.activate(['files', 'commands'])
    return Workspace(session)


def test_files_roundtrip_edit_copy_move_and_delete(workspace, tmp_path):
    path = tmp_path / 'acentos.txt'
    workspace.call('write', path=str(path), text='Olá, mundo!')
    assert workspace.call('read', path=str(path))['content'] == 'Olá, mundo!'
    assert workspace.call('edit', path=str(path), old_text='mundo', new_text='Willson')['replacements'] == 1
    with pytest.raises(ValueError, match='não encontrado'):
        workspace.call('edit', path=str(path), old_text='missing', new_text='wrong')
    copy = tmp_path / 'copy.txt'
    workspace.call('copy', source=str(path), destination=str(copy))
    assert copy.read_text(encoding='utf-8') == 'Olá, Willson!'
    moved = tmp_path / 'moved.txt'
    workspace.call('move', source=str(copy), destination=str(moved))
    assert not copy.exists()
    assert moved.exists()
    entries = workspace.call('list', path=str(tmp_path))['entries']
    assert {'acentos.txt', 'moved.txt'} <= {item['name'] for item in entries}
    workspace.call('delete', path=str(moved))
    assert not moved.exists()


def test_existing_files_are_preserved(workspace, tmp_path):
    path = tmp_path / 'existing.txt'
    path.write_text('preserve')
    with pytest.raises(FileExistsError):
        workspace.call('write', path=str(path), text='replace')
    assert path.read_text() == 'preserve'
    workspace.call('write', path=str(path), text='replace', overwrite=True)
    assert path.read_text() == 'replace'


def test_ambiguous_edit_does_not_change_file(workspace, tmp_path):
    path = tmp_path / 'data.txt'
    path.write_text('one one')
    with pytest.raises(ValueError, match='mais de uma vez'):
        workspace.call('edit', path=str(path), old_text='one', new_text='two')
    assert path.read_text() == 'one one'
    result = workspace.call('edit', path=str(path), old_text='one', new_text='two', replace_all=True)
    assert result['replacements'] == 2
    assert path.read_text() == 'two two'


def test_binary_upload_download_roundtrip_and_limits(workspace, tmp_path):
    data = bytes(range(256))
    path = tmp_path / 'binary.dat'
    workspace.call('write_binary', path=str(path), content_base64=base64.b64encode(data).decode())
    received = workspace.call('read_binary', path=str(path))
    assert base64.b64decode(received['content_base64']) == data
    with pytest.raises(ValueError, match='não foi retornado'):
        workspace.call('read_binary', path=str(path), max_bytes=100)
    with pytest.raises(ValueError, match='Base64 inválido'):
        workspace.call('write_binary', path=str(tmp_path / 'bad'), content_base64='not base64@@@')


def test_recursive_delete_is_explicit(workspace, tmp_path):
    path = tmp_path / 'directory'
    workspace.call('mkdir', path=str(path))
    (path / 'child').write_text('x')
    with pytest.raises(OSError):
        workspace.call('delete', path=str(path))
    assert path.exists()
    workspace.call('delete', path=str(path), recursive=True)
    assert not path.exists()


def test_directory_cannot_be_copied_into_itself(workspace, tmp_path):
    source = tmp_path / 'directory'
    source.mkdir()
    (source / 'file').write_text('preserve')
    with pytest.raises(ValueError, match='dentro da pasta'):
        workspace.call('copy', source=str(source), destination=str(source / 'child'))
    assert not (source / 'child').exists()


def test_copy_directory_and_its_contents(workspace, tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'file').write_text('copied')
    destination = tmp_path / 'destination'
    workspace.call('copy', source=str(source), destination=str(destination))
    assert (destination / 'file').read_text() == 'copied'


def test_read_truncation_keeps_utf8_boundary(workspace, tmp_path):
    path = tmp_path / 'utf8.txt'
    path.write_text('áá', encoding='utf-8')
    result = workspace.call('read', path=str(path), max_bytes=3)
    assert result['content'] == 'á'
    assert result['truncated']


def test_permissions_are_independent(workspace, tmp_path):
    workspace.session.activate(['files'])
    with pytest.raises(PermissionError):
        workspace.call('run', command='print(1)', shell='python')
    workspace.session.activate(['commands'])
    with pytest.raises(PermissionError):
        workspace.call('list', path=str(tmp_path))


@pytest.mark.parametrize('operation', ['read', 'read_binary', 'mkdir'])
def test_queued_operation_rechecks_permission_after_lock(workspace, tmp_path, operation):
    class ObservedLock:
        def __init__(self):
            self.lock = threading.RLock()
            self.attempted = threading.Event()
        def __enter__(self):
            self.attempted.set()
            self.lock.acquire()
        def __exit__(self, *args):
            self.lock.release()
    workspace.lock = lock = ObservedLock()
    path = tmp_path / ('new-directory' if operation == 'mkdir' else 'secret.txt')
    if operation != 'mkdir':
        path.write_text('private content', encoding='utf-8')
    results, errors = [], []
    def work():
        try:
            results.append(workspace.call(operation, path=str(path)))
        except BaseException as error:
            errors.append(error)
    with lock:
        lock.attempted.clear()
        thread = threading.Thread(target=work)
        thread.start()
        assert lock.attempted.wait(2), 'Worker never attempted the held operation lock'
        workspace.session.stop()
    thread.join(2)
    assert not thread.is_alive()
    assert not results
    assert len(errors) == 1 and isinstance(errors[0], PermissionError)
    if operation == 'mkdir':
        assert not path.exists()


@pytest.mark.parametrize('operation', ['read', 'read_binary'])
def test_revocation_during_read_does_not_return_payload(workspace, tmp_path, monkeypatch, operation):
    path = tmp_path / 'private.txt'
    path.write_text('private content', encoding='utf-8')
    original = getattr(workspace, '_' + operation)
    def revoke_after_read(**args):
        result = original(**args)
        workspace.session.stop()
        return result
    monkeypatch.setattr(workspace, '_' + operation, revoke_after_read)
    with pytest.raises(PermissionError):
        workspace.call(operation, path=str(path))


@pytest.mark.parametrize('overwrite', [False, True])
def test_cancelled_save_preserves_original_and_removes_staging(workspace, tmp_path, monkeypatch, overwrite):
    path = tmp_path / 'destination'
    if overwrite:
        path.write_text('original', encoding='utf-8')
    original_fsync = os.fsync
    def revoke_at_flush(fd):
        original_fsync(fd)
        workspace.session.stop()
    monkeypatch.setattr(os, 'fsync', revoke_at_flush)
    with pytest.raises(PermissionError):
        workspace.call('write', path=str(path), text='replacement', overwrite=overwrite)
    if overwrite:
        assert path.read_text(encoding='utf-8') == 'original'
    else:
        assert not path.exists()
    assert not list(tmp_path.glob('.navix-*'))


def test_move_does_not_overwrite_destination_created_during_race(workspace, tmp_path, monkeypatch):
    source, destination = tmp_path / 'source', tmp_path / 'destination'
    source.write_text('original')
    original_rename = workspace._rename_exclusive
    def concurrent_destination(src, dst):
        dst.write_text('concurrent')
        return original_rename(src, dst)
    monkeypatch.setattr(workspace, '_rename_exclusive', concurrent_destination)
    with pytest.raises(FileExistsError):
        workspace.call('move', source=str(source), destination=str(destination))
    assert source.read_text() == 'original'
    assert destination.read_text() == 'concurrent'


def test_move_keeps_source_if_revoked_before_atomic_move(workspace, tmp_path, monkeypatch):
    source, destination = tmp_path / 'source', tmp_path / 'destination'
    source.write_text('original')
    original_move = workspace._move_atomic
    def revoke_before_move(src, dst, overwrite=False):
        workspace.session.stop()
        return original_move(src, dst, overwrite=overwrite)
    monkeypatch.setattr(workspace, '_move_atomic', revoke_before_move)
    with pytest.raises(PermissionError):
        workspace.call('move', source=str(source), destination=str(destination))
    assert source.read_text() == 'original'
    assert not destination.exists()


def test_atomic_directory_move_keeps_child_created_at_rename(workspace, tmp_path, monkeypatch):
    source, destination = tmp_path / 'source', tmp_path / 'destination'
    source.mkdir()
    (source / 'existing').write_text('original')
    original_rename = workspace._rename_exclusive
    def create_child_then_rename(src, dst):
        (src / 'new-child').write_text('created during move')
        (src / 'existing').write_text('modified during move')
        return original_rename(src, dst)
    monkeypatch.setattr(workspace, '_rename_exclusive', create_child_then_rename)
    monkeypatch.setattr(workspace, '_copy_tree', lambda *args: pytest.fail('Move must not copy/delete a tree'))
    workspace.call('move', source=str(source), destination=str(destination))
    assert not source.exists()
    assert (destination / 'new-child').read_text() == 'created during move'
    assert (destination / 'existing').read_text() == 'modified during move'


def test_cross_volume_move_preserves_new_source_children(workspace, tmp_path, monkeypatch):
    source, destination = tmp_path / 'source', tmp_path / 'destination'
    source.mkdir()
    (source / 'existing').write_text('original')
    def unavailable_rename(src, dst):
        (src / 'new-child').write_text('new data')
        raise OSError(errno.EXDEV, 'Different volumes')
    monkeypatch.setattr(workspace, '_rename_exclusive', unavailable_rename)
    monkeypatch.setattr(workspace, '_copy_tree', lambda *args: pytest.fail('Cross-volume move must not copy/delete'))
    with pytest.raises(RuntimeError, match='origem foi preservada'):
        workspace.call('move', source=str(source), destination=str(destination))
    assert (source / 'existing').read_text() == 'original'
    assert (source / 'new-child').read_text() == 'new data'
    assert not destination.exists()


def test_copy_fallback_without_hardlinks(workspace, tmp_path, monkeypatch):
    source, destination = tmp_path / 'source', tmp_path / 'destination'
    source.write_text('read-only source')
    source.chmod(0o444)
    def unsupported_links(*args, **kwargs):
        raise OSError(errno.EXDEV, 'hard links unsupported')
    monkeypatch.setattr(os, 'link', unsupported_links)
    workspace.call('copy', source=str(source), destination=str(destination))
    assert destination.read_text() == 'read-only source'
    assert not list(tmp_path.glob('.navix-copy-*'))


def test_fallback_keeps_concurrent_destination(workspace, tmp_path, monkeypatch):
    source, destination = tmp_path / 'source', tmp_path / 'destination'
    source.write_text('original')
    def concurrent_destination(*args, **kwargs):
        destination.write_text('concurrent')
        raise OSError(errno.EXDEV, 'hard links unsupported')
    monkeypatch.setattr(os, 'link', concurrent_destination)
    if os.name == 'nt':
        pytest.skip('Windows uses exclusive rename instead of hard links')
    with pytest.raises(FileExistsError):
        workspace.call('copy', source=str(source), destination=str(destination))
    assert destination.read_text() == 'concurrent'
    assert source.read_text() == 'original'


def test_real_python_command_and_explicit_argv(workspace, tmp_path):
    result = workspace.call('run', command="import os; print('Olá'); print(os.getcwd())", shell='python', cwd=str(tmp_path))
    assert result['exit_code'] == 0
    # Force explicit UTF-8 in the subprocess so Windows locale cannot corrupt it.
    result = workspace.call('exec', argv=[sys.executable, '-X', 'utf8', '-c', "print('Olá')"])
    assert result['stdout'].strip() == 'Olá'
    assert not result['timed_out']


def test_command_timeout_kills_process_before_later_side_effect(workspace, tmp_path):
    marker = tmp_path / 'marker'
    command = 'import pathlib,time; time.sleep(2); pathlib.Path(%r).write_text("wrong")' % str(marker)
    result = workspace.call('run', command=command, shell='python', timeout_seconds=1)
    assert result['timed_out']
    time.sleep(1.2)
    assert not marker.exists()


def test_revocation_kills_running_command(workspace, tmp_path):
    marker = tmp_path / 'marker'
    errors = []
    command = 'import pathlib,time; time.sleep(1); pathlib.Path(%r).write_text("wrong")' % str(marker)
    def work():
        try:
            workspace.call('run', command=command, shell='python')
        except BaseException as error:
            errors.append(error)
    thread = threading.Thread(target=work)
    thread.start()
    time.sleep(.15)
    workspace.session.stop()
    thread.join(3)
    assert not thread.is_alive()
    assert len(errors) == 1 and isinstance(errors[0], PermissionError)
    time.sleep(1)
    assert not marker.exists()


def test_revocation_kills_descendant_process(workspace, tmp_path):
    marker = tmp_path / 'descendant-marker'
    child = 'import pathlib,time; time.sleep(1.2); pathlib.Path(%r).write_text("wrong")' % str(marker)
    parent = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",%r]); time.sleep(5)' % child
    errors = []
    def work():
        try:
            workspace.call('run', command=parent, shell='python')
        except BaseException as error:
            errors.append(error)
    thread = threading.Thread(target=work)
    thread.start()
    time.sleep(.2)
    workspace.session.stop()
    thread.join(3)
    assert not thread.is_alive()
    assert len(errors) == 1 and isinstance(errors[0], PermissionError)
    time.sleep(1.3)
    assert not marker.exists()


def test_output_limit_is_observable(workspace):
    result = workspace.call('run', command="print('x' * 1100000)", shell='python')
    assert len(result['stdout']) <= 1_000_000
    assert result['output_truncated']


def test_frozen_executable_is_not_used_as_python(workspace, monkeypatch):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr('navix.workspace.shutil.which', lambda name: None)
    with pytest.raises(RuntimeError, match='Interpretador Python não encontrado'):
        workspace.call('run', command='print(1)', shell='python')


def test_frozen_python_prefers_bundled_console_runner(workspace, tmp_path, monkeypatch):
    executable = tmp_path / 'NavixDesktop.exe'
    runtime = tmp_path / 'python-runtime' / 'NavixPython.exe'
    runtime.parent.mkdir()
    runtime.write_bytes(b'fixture')
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(executable))
    monkeypatch.setattr('navix.workspace.shutil.which', lambda name: '/wrong/installed/python')
    assert workspace._python() == [str(runtime)]


def test_http_download_and_failed_download_preserves_destination(workspace, tmp_path):
    payload = b'navix-download-content'
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = 'http://127.0.0.1:%d/file' % server.server_address[1]
        destination = tmp_path / 'download'
        result = workspace.call('download', url=url, destination=str(destination))
        assert destination.read_bytes() == payload
        assert result['size_bytes'] == len(payload)
        with pytest.raises(ValueError, match='excede o limite'):
            workspace.call('download', url=url, destination=str(destination), overwrite=True, max_bytes=1)
        assert destination.read_bytes() == payload
        assert not list(tmp_path.glob('.navix-download-*'))
    finally:
        server.shutdown()
        server.server_close()


def test_file_scheme_download_is_rejected(workspace, tmp_path):
    with pytest.raises(ValueError, match='HTTP/HTTPS'):
        workspace.call('download', url='file:///etc/passwd', destination=str(tmp_path / 'bad'))

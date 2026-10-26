"""Files, transfers and command execution for an authorized local session.

The methods deliberately return data, never print it: the MCP audit records only
the operation name/result, not file contents, commands, URLs or credentials.
"""
import base64
import binascii
import ctypes
import errno
import hashlib
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


TEXT_LIMIT = 5_000_000
BINARY_LIMIT = 10_000_000
OUTPUT_LIMIT = 1_000_000


def _path(value):
    if not isinstance(value, str) or not value.strip() or '\x00' in value:
        raise ValueError('Informe um caminho válido.')
    return Path(os.path.expandvars(value)).expanduser().absolute()


def _bounded_integer(value, minimum, maximum, label):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError('%s deve ser um inteiro de %d a %d.' % (label, minimum, maximum))
    return value


def _web_url(value):
    parts = urlsplit(value)
    if parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password:
        raise ValueError('Use uma URL HTTP/HTTPS sem credenciais embutidas.')
    return value


class _WebRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        _web_url(new_url)
        return super().redirect_request(request, fp, code, message, headers, new_url)


class Workspace:
    def __init__(self, session):
        self.session = session
        self.lock = threading.RLock()

    def call(self, operation, **args):
        if operation in {'run', 'exec'}:
            self.session.require('commands')
            result = self._run(operation, args)
            self.session.require('commands')
            return result
        with self.lock:
            # A request may have waited behind a download/copy for minutes.
            # Authorize when it actually starts, not before it joins the queue.
            self.session.require('files')
            if operation == 'list':
                result = self._list(**args)
            elif operation == 'read':
                result = self._read(**args)
            elif operation == 'read_binary':
                result = self._read_binary(**args)
            elif operation == 'write':
                result = self._write(**args)
            elif operation == 'write_binary':
                result = self._write_binary(**args)
            elif operation == 'edit':
                result = self._edit(**args)
            elif operation == 'mkdir':
                path = _path(args['path'])
                self.session.require('files')
                path.mkdir(parents=args.get('parents', True), exist_ok=True)
                result = {'path': str(path), 'created': True}
            elif operation in {'copy', 'move'}:
                result = self._copy_or_move(operation, **args)
            elif operation == 'delete':
                result = self._delete(**args)
            elif operation == 'download':
                result = self._download(**args)
            else:
                raise ValueError('Operação desconhecida.')
            # A revocation while reading must not release the captured contents.
            self.session.require('files')
            return result

    def _list(self, path, limit=500):
        path = _path(path)
        _bounded_integer(limit, 1, 2000, 'Limite')
        entries = []
        truncated = False
        # Do not sort a potentially enormous directory before applying the limit.
        with os.scandir(path) as iterator:
            for item in iterator:
                self.session.require('files')
                if len(entries) == limit:
                    truncated = True
                    break
                entry = {'name': item.name, 'path': item.path,
                         'type': 'directory' if item.is_dir() else 'file',
                         'is_symlink': item.is_symlink()}
                try:
                    info = item.stat(follow_symlinks=False)
                    entry.update(size_bytes=info.st_size, modified=info.st_mtime)
                except OSError:
                    entry['unavailable'] = True
                entries.append(entry)
        return {'path': str(path), 'entries': sorted(entries, key=lambda row: row['name'].casefold()),
                'truncated': truncated}

    def _read(self, path, max_bytes=1_000_000):
        path = _path(path)
        _bounded_integer(max_bytes, 1, TEXT_LIMIT, 'Máximo de bytes')
        with path.open('rb') as stream:
            data = stream.read(max_bytes + 1)
        truncated = len(data) > max_bytes
        data = data[:max_bytes]
        try:
            # An incremental decoder tolerates only an incomplete final UTF-8
            # character at the truncation boundary, never invalid binary data.
            import codecs
            decoder = codecs.getincrementaldecoder('utf-8-sig')()
            content = decoder.decode(data, final=not truncated)
        except UnicodeDecodeError as error:
            raise ValueError('Arquivo não é texto UTF-8; use a leitura binária.') from error
        return {'path': str(path), 'content': content, 'truncated': truncated,
                'size_bytes': path.stat().st_size}

    def _read_binary(self, path, max_bytes=5_000_000):
        path = _path(path)
        _bounded_integer(max_bytes, 1, BINARY_LIMIT, 'Máximo de bytes')
        with path.open('rb') as stream:
            data = stream.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError('Arquivo excede o limite; não foi retornado um arquivo parcial.')
        return {'path': str(path), 'content_base64': base64.b64encode(data).decode('ascii'),
                'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def _save(self, path, data, overwrite):
        self.session.require('files')
        fd, temporary = tempfile.mkstemp(prefix='.navix-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                for offset in range(0, len(data), 64 * 1024):
                    self.session.require('files')
                    stream.write(data[offset:offset + 64 * 1024])
                stream.flush()
                os.fsync(stream.fileno())
            self.session.require('files')
            self._publish(temporary, path, overwrite)
        finally:
            self._cleanup_staged(temporary)
        return {'path': str(path), 'size_bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest()}

    def _write(self, path, text, overwrite=False):
        if not isinstance(text, str):
            raise ValueError('O conteúdo deve ser texto.')
        data = text.encode('utf-8')
        if len(data) > TEXT_LIMIT:
            raise ValueError('Texto excede cinco milhões de bytes por chamada.')
        return self._save(_path(path), data, overwrite)

    def _write_binary(self, path, content_base64, overwrite=False):
        if not isinstance(content_base64, str) or len(content_base64) > ((BINARY_LIMIT + 2) // 3) * 4:
            raise ValueError('Conteúdo binário ausente ou excede dez milhões de bytes.')
        try:
            data = base64.b64decode(content_base64, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError('Conteúdo Base64 inválido.') from error
        if len(data) > BINARY_LIMIT:
            raise ValueError('Conteúdo binário excede dez milhões de bytes.')
        return self._save(_path(path), data, overwrite)

    def _edit(self, path, old_text, new_text, replace_all=False):
        if not isinstance(old_text, str) or not old_text or not isinstance(new_text, str):
            raise ValueError('Informe trecho original não vazio e novo texto.')
        result = self._read(path, max_bytes=TEXT_LIMIT)
        if result['truncated']:
            raise ValueError('Arquivo grande demais para edição textual nesta chamada.')
        content = result['content']
        count = content.count(old_text)
        if count == 0:
            raise ValueError('Trecho original não encontrado; nenhuma alteração foi feita.')
        if count > 1 and not replace_all:
            raise ValueError('Trecho aparece mais de uma vez. Use trecho único ou replace_all.')
        saved = self._write(path, content.replace(old_text, new_text), overwrite=True)
        saved['replacements'] = count
        return saved

    def _copy_or_move(self, operation, source, destination, overwrite=False):
        source, destination = _path(source), _path(destination)
        if source == destination:
            raise ValueError('Origem e destino devem ser diferentes.')
        if source.is_dir() and destination.resolve().is_relative_to(source.resolve()):
            raise ValueError('Destino não pode estar dentro da pasta de origem.')
        if destination.exists() or destination.is_symlink():
            if not overwrite:
                raise FileExistsError(str(destination))
            if destination.is_dir():
                raise IsADirectoryError('Destino já é uma pasta; escolha um caminho novo.')
            if source.is_dir():
                raise FileExistsError('Não substitua um arquivo por uma pasta implicitamente.')
        self.session.require('files')
        if operation == 'move':
            self._move_atomic(source, destination, overwrite)
            return {'source': str(source), 'destination': str(destination), 'ok': True}
        is_directory = source.is_dir() and not source.is_symlink()
        if source.is_symlink():
            self._copy_symlink(source, destination, overwrite=overwrite)
        elif is_directory:
            self._copy_tree(source, destination)
        else:
            self._copy_file(source, destination, overwrite=overwrite)
        return {'source': str(source), 'destination': str(destination), 'ok': True}

    def _move_atomic(self, source, destination, overwrite=False):
        self.session.require('files')
        try:
            if overwrite:
                os.replace(source, destination)
            else:
                self._rename_exclusive(source, destination)
        except OSError as error:
            if error.errno in {errno.EXDEV, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS} or getattr(error, 'winerror', None) == 17:
                raise RuntimeError('Movimentação atômica indisponível entre estes volumes ou neste '
                                   'sistema de arquivos. A origem foi preservada; copie, confira o '
                                   'resultado e solicite a exclusão separadamente.') from error
            raise

    def _rename_exclusive(self, source, destination):
        if os.name == 'nt':
            # Windows rename fails if destination exists; the entire directory
            # tree is renamed atomically, including files created before it.
            os.rename(source, destination)
            return
        if sys.platform.startswith('linux'):
            # POSIX os.rename can silently replace a concurrently-created target.
            # Linux exposes an exclusive atomic rename that avoids copy/delete
            # races and preserves source mutations up to the rename itself.
            libc = ctypes.CDLL(None, use_errno=True)
            rename = getattr(libc, 'renameat2', None)
            if rename is not None:
                rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                   ctypes.c_char_p, ctypes.c_uint]
                rename.restype = ctypes.c_int
                if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1) == 0:
                    return
                number = ctypes.get_errno()
                raise OSError(number, os.strerror(number), str(destination))
        raise OSError(errno.ENOTSUP, 'Exclusive atomic rename is unavailable')

    def _copy_tree(self, source, destination):
        self.session.require('files')
        destination.mkdir()  # Exclusive: never merge into a concurrent folder.
        with os.scandir(source) as iterator:
            for entry in iterator:
                self.session.require('files')
                incoming = source / entry.name
                outgoing = destination / entry.name
                if entry.is_symlink():
                    self._copy_symlink(incoming, outgoing)
                elif entry.is_dir(follow_symlinks=False):
                    self._copy_tree(incoming, outgoing)
                else:
                    self._copy_file(incoming, outgoing)
        self.session.require('files')
        shutil.copystat(source, destination)

    def _copy_symlink(self, source, destination, overwrite=False):
        self.session.require('files')
        if not overwrite:
            destination.symlink_to(os.readlink(source), target_is_directory=source.is_dir())
            return
        with tempfile.TemporaryDirectory(prefix='.navix-link-', dir=destination.parent) as directory:
            staged = Path(directory) / 'link'
            staged.symlink_to(os.readlink(source), target_is_directory=source.is_dir())
            self.session.require('files')
            os.replace(staged, destination)

    def _remove_tree(self, path):
        self.session.require('files')
        with os.scandir(path) as iterator:
            for entry in iterator:
                self.session.require('files')
                child = path / entry.name
                if entry.is_dir(follow_symlinks=False):
                    self._remove_tree(child)
                else:
                    child.unlink()
        self.session.require('files')
        path.rmdir()

    def _copy_file(self, source, destination, overwrite=False):
        fd, temporary = tempfile.mkstemp(prefix='.navix-copy-', dir=destination.parent)
        try:
            with os.fdopen(fd, 'wb') as outgoing, source.open('rb') as incoming:
                while True:
                    self.session.require('files')
                    block = incoming.read(64 * 1024)
                    if not block:
                        break
                    outgoing.write(block)
            shutil.copystat(source, temporary)
            self.session.require('files')
            self._publish(temporary, destination, overwrite)
            return str(destination)
        finally:
            self._cleanup_staged(temporary)

    def _cleanup_staged(self, path):
        if os.path.exists(path):
            if os.name == 'nt':
                # Windows cannot unlink a read-only staged copy. Windows uses
                # rename below, never a hard link, so this cannot change the
                # published destination's attributes through a shared inode.
                os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
            os.unlink(path)

    def _publish(self, temporary, destination, overwrite=False):
        self.session.require('files')
        if overwrite:
            os.replace(temporary, destination)
            return
        if os.name == 'nt':
            # Windows rename is exclusive even on FAT/exFAT, unlike POSIX
            # rename, and moves read-only files without needing to unlink them.
            os.rename(temporary, destination)
            return
        try:
            os.link(temporary, destination)
        except OSError as error:
            if error.errno not in {errno.EXDEV, errno.EPERM, errno.EOPNOTSUPP, errno.ENOSYS}:
                raise
            # Filesystems without hard links still support exclusive creation.
            # The fallback is cancellable and removes only its own partial file.
            identity = None
            try:
                with open(temporary, 'rb') as source, open(destination, 'xb') as target:
                    identity = os.fstat(target.fileno())
                    while True:
                        self.session.require('files')
                        block = source.read(64 * 1024)
                        if not block:
                            break
                        target.write(block)
                self.session.require('files')
                shutil.copystat(temporary, destination)
            except BaseException:
                if identity is not None:
                    try:
                        current = os.stat(destination, follow_symlinks=False)
                        if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                            os.unlink(destination)
                    except FileNotFoundError:
                        pass
                raise

    def _delete(self, path, recursive=False):
        path = _path(path)
        self.session.require('files')
        if path.is_symlink() or not path.is_dir():
            path.unlink()
        elif recursive:
            self._remove_tree(path)
        else:
            path.rmdir()  # A non-empty folder needs an explicit recursive=True.
        return {'path': str(path), 'deleted': True}

    def _download(self, url, destination, overwrite=False, max_bytes=100_000_000,
                  timeout_seconds=30):
        _web_url(url)
        _bounded_integer(max_bytes, 1, 1_000_000_000, 'Máximo de bytes')
        _bounded_integer(timeout_seconds, 1, 120, 'Tempo limite')
        destination = _path(destination)
        if (destination.exists() or destination.is_symlink()) and not overwrite:
            raise FileExistsError(str(destination))
        fd, temporary = tempfile.mkstemp(prefix='.navix-download-', dir=destination.parent)
        started = time.monotonic()
        size = 0
        digest = hashlib.sha256()
        try:
            with os.fdopen(fd, 'wb') as stream:
                request = Request(url, headers={'User-Agent': 'NavixDesktop/0.2'})
                with build_opener(_WebRedirects()).open(request, timeout=min(timeout_seconds, 5)) as response:
                    _web_url(response.url)
                    length = response.headers.get('Content-Length')
                    if length and int(length) > max_bytes:
                        raise ValueError('Download excede o limite configurado.')
                    while True:
                        self.session.require('files')
                        if time.monotonic() - started > timeout_seconds:
                            raise TimeoutError('Download excedeu o tempo limite.')
                        block = response.read(64 * 1024)
                        if not block:
                            break
                        size += len(block)
                        if size > max_bytes:
                            raise ValueError('Download excede o limite configurado.')
                        stream.write(block)
                        digest.update(block)
            self.session.require('files')
            self._publish(temporary, destination, overwrite)
            return {'path': str(destination), 'size_bytes': size, 'sha256': digest.hexdigest()}
        finally:
            self._cleanup_staged(temporary)

    def _python(self):
        if not getattr(sys, 'frozen', False):
            return [sys.executable]
        bundled = Path(sys.executable).parent / 'python-runtime' / 'NavixPython.exe'
        if bundled.is_file():
            return [str(bundled)]
        # PyInstaller's executable launches the panel, not a Python interpreter.
        for name, suffix in [('py', ['-3']), ('python', []), ('python3', [])]:
            executable = shutil.which(name)
            if executable and 'windowsapps' not in executable.lower():
                return [executable] + suffix
        raise RuntimeError('Interpretador Python não encontrado. O Python interno do aplicativo '
                           'não executa scripts externos; instale um interpretador Python.')

    def _argv(self, operation, args):
        if operation == 'exec':
            argv = args['argv']
            if (not isinstance(argv, list) or not argv or len(argv) > 1000 or
                    any(not isinstance(value, str) or '\x00' in value for value in argv) or not argv[0]):
                raise ValueError('Informe uma lista não vazia de programa e argumentos válidos.')
            return argv
        command = args['command']
        if not isinstance(command, str) or not command.strip() or len(command) > 100_000 or '\x00' in command:
            raise ValueError('Informe um comando não vazio de até 100 mil caracteres.')
        shell = args.get('shell', 'powershell')
        if shell == 'python':
            return self._python() + ['-c', command]
        if shell == 'powershell':
            executable = shutil.which('pwsh') or shutil.which('powershell')
            if not executable:
                raise RuntimeError('PowerShell não encontrado neste computador.')
            command = ('[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding; '
                       '$OutputEncoding = [Console]::OutputEncoding; ' + command)
            return [executable, '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', command]
        if shell == 'cmd' and os.name == 'nt':
            return [os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/s', '/c', 'chcp 65001>nul & ' + command]
        if shell in {'sh', 'bash'} and os.name != 'nt':
            executable = shutil.which(shell)
            if executable:
                return [executable, '-c', command]
        raise ValueError('Shell indisponível. Use powershell, cmd ou python no Windows.')

    def _kill_tree(self, process):
        if os.name == 'nt':
            taskkill = shutil.which('taskkill')
            if taskkill:
                try:
                    subprocess.run([taskkill, '/PID', str(process.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=5, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            if process.poll() is None:
                process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def _run(self, operation, args):
        timeout = _bounded_integer(args.get('timeout_seconds', 60), 1, 300, 'Tempo limite')
        cwd = str(_path(args['cwd'])) if args.get('cwd') else None
        argv = self._argv(operation, args)
        options = {'start_new_session': True} if os.name != 'nt' else {
            'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
        started = time.monotonic()
        timed_out = exceeded = False
        # Real files avoid deadlocks on a full stdout pipe and let us check the
        # output budget while the process is running.
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            self.session.require('commands')
            environment = os.environ.copy()
            environment.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
            process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, env=environment, **options)
            try:
                while process.poll() is None:
                    self.session.require('commands')
                    timed_out = time.monotonic() - started >= timeout
                    exceeded = (os.fstat(stdout.fileno()).st_size > OUTPUT_LIMIT or
                                os.fstat(stderr.fileno()).st_size > OUTPUT_LIMIT)
                    if timed_out or exceeded:
                        self._kill_tree(process)
                        break
                    time.sleep(.05)
                self.session.require('commands')
            except BaseException:
                self._kill_tree(process)
                raise
            stdout.seek(0)
            stderr.seek(0)
            out, err = stdout.read(OUTPUT_LIMIT + 1), stderr.read(OUTPUT_LIMIT + 1)
        truncated = len(out) > OUTPUT_LIMIT or len(err) > OUTPUT_LIMIT
        return {'exit_code': process.returncode, 'stdout': out[:OUTPUT_LIMIT].decode('utf-8', errors='replace'),
                'stderr': err[:OUTPUT_LIMIT].decode('utf-8', errors='replace'),
                'timed_out': timed_out, 'output_truncated': exceeded or truncated,
                'duration_seconds': round(time.monotonic() - started, 3)}

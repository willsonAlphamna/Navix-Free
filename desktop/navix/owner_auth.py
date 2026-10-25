"""Optional *local* panel login for the Windows user who owns NavixX.

This is not an OpenAI account, an online identity provider, or a replacement
for MCP authorization. It only gates the native control panel on this PC.
"""

import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time


_ITERATIONS = 240_000


class OwnerAccount:
    """PBKDF2-hashed local password, constant-time checks and retry delays."""

    def __init__(self, directory, clock=time.monotonic):
        self.path = Path(directory) / 'owner-login.json'
        self.clock = clock
        self.failures = 0
        self.blocked_until = 0.0

    @property
    def exists(self):
        return self.path.is_file()

    @staticmethod
    def _derive(password, salt, iterations):
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt,
                                   iterations, dklen=32)

    def enroll(self, password):
        if self.exists:
            raise ValueError('Já existe um login local neste perfil do Windows.')
        if len(password) < 10:
            raise ValueError('Use uma senha com pelo menos 10 caracteres.')
        salt = secrets.token_bytes(24)
        data = {'version': 1, 'method': 'pbkdf2-sha256', 'iterations': _ITERATIONS,
                'salt': salt.hex(),
                'digest': self._derive(password, salt, _ITERATIONS).hex()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents replacing an existing password by mistake.
        with self.path.open('x', encoding='utf-8') as handle:
            json.dump(data, handle)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass  # LocalAppData is already scoped to this Windows profile.

    def verify(self, password):
        if not self.exists or self.clock() < self.blocked_until:
            return False
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if data.get('version') != 1 or data.get('method') != 'pbkdf2-sha256':
                return False
            salt = bytes.fromhex(data['salt'])
            digest = bytes.fromhex(data['digest'])
            iterations = int(data['iterations'])
            if len(salt) != 24 or len(digest) != 32 or not 100_000 <= iterations <= 800_000:
                return False
            valid = hmac.compare_digest(self._derive(password, salt, iterations), digest)
        except (OSError, ValueError, TypeError, KeyError):
            valid = False
        if valid:
            self.failures = 0
            self.blocked_until = 0.0
        else:
            self.failures += 1
            if self.failures >= 5:
                self.blocked_until = self.clock() + 30
                self.failures = 0
        return valid

    def seconds_until_retry(self):
        return max(0, int(self.blocked_until - self.clock() + 0.999))

"""Windows device enrollment for the single public NavixX MCP plugin.

Each device generates its own secret; the user enters a short code while
signed in to the service. No OpenAI tunnel/API key is created on customer PCs.
"""
from dataclasses import dataclass
import json
from pathlib import Path
import re
import secrets
from urllib import request as urlrequest
from urllib.parse import urlencode, urlsplit, urlunsplit

from .cloud import CloudSettings


_DEVICE = re.compile(r'^[A-Za-z0-9_-]{16,128}$')
_SECRET = re.compile(r'^[A-Za-z0-9_-]{43,128}$')


@dataclass(frozen=True)
class DeviceIdentity:
    device_id: str
    agent_secret: str

    def validate(self):
        if not _DEVICE.fullmatch(self.device_id) or not _SECRET.fullmatch(self.agent_secret):
            raise ValueError('Identidade do computador inválida.')


class DeviceIdentityStore:
    """LocalAppData DPAPI: private to this Windows account; never email the token."""
    def __init__(self, directory):
        self.path = Path(directory) / 'cloud-device.dat'

    def load(self):
        try:
            from .tunnel_manager import _dpapi
            obj = json.loads(_dpapi(self.path.read_bytes(), False))
            result = DeviceIdentity(obj['device_id'], obj['agent_secret'])
            result.validate()
            return result
        except (OSError, ValueError, KeyError, TypeError, UnicodeError):
            return None

    def ensure(self):
        existing = self.load()
        if existing:
            return existing
        identity = DeviceIdentity(secrets.token_urlsafe(20), secrets.token_urlsafe(32))
        identity.validate()
        from .tunnel_manager import _dpapi
        data = _dpapi(json.dumps(vars(identity)).encode('utf-8'), True)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open('xb') as handle:
                handle.write(data)
        except FileExistsError:
            result = self.load()
            if result:
                return result
            raise RuntimeError('Identidade existente não pode ser recuperada.')
        return identity


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirecionamento não permitido no pareamento.')


class PairingHttpClient:
    """HTTPS only, bounded responses, no forwarding of device credentials."""
    def __init__(self, settings: CloudSettings, opener=None):
        settings.validate()
        if not settings.enabled:
            raise ValueError('Integração cloud está desligada.')
        parsed = urlsplit(settings.relay_url)
        self.base = urlunsplit(('https', parsed.netloc, '', '', ''))
        self.opener = opener or urlrequest.build_opener(_NoRedirect,
                                                      urlrequest.ProxyHandler({}))

    def _json(self, path, body=None, agent_secret=None):
        if agent_secret is not None and not _SECRET.fullmatch(agent_secret):
            raise ValueError('Credencial do dispositivo inválida.')
        request = urlrequest.Request(self.base + path,
            data=json.dumps(body).encode('utf-8') if body is not None else None,
            headers={
                'Accept': 'application/json',
                **({'Content-Type':'application/json'} if body is not None else {}),
                **({'X-Navix-Agent-Token':agent_secret} if agent_secret else {}),
            }, method='POST' if body is not None else 'GET')
        with self.opener.open(request, timeout=12) as response:
            data = response.read(4097)
            if len(data)>4096: raise ValueError('Resposta excessiva do serviço.')
            return json.loads(data.decode('utf-8'))

    def begin(self, identity: DeviceIdentity):
        identity.validate()
        code=f'{secrets.randbelow(1000000):06d}'
        result=self._json('/api/pair/start',{
            'device_id': identity.device_id,
            'agent_secret':identity.agent_secret,
            'code':code,
        })
        if result.get('deviceId') != identity.device_id or not isinstance(result.get('expiresAt'),int):
            raise RuntimeError('Não foi possível iniciar pareamento.')
        return {'device_id':identity.device_id,'verification_code':code,
                'expires_at':result['expiresAt']}

    def renew(self, identity: DeviceIdentity):
        """Fresh device-proof for another ChatGPT authorization, no new secrets."""
        identity.validate()
        code=f'{secrets.randbelow(1000000):06d}'
        result=self._json('/api/pair/renew',{
            'device_id':identity.device_id,'code':code,
        },agent_secret=identity.agent_secret)
        if result.get('deviceId')!=identity.device_id or not isinstance(result.get('expiresAt'),int):
            raise RuntimeError('Não foi possível gerar novo código.')
        return {'device_id':identity.device_id,'verification_code':code,
                'expires_at':result['expiresAt']}

    def status(self, identity: DeviceIdentity):
        identity.validate()
        result=self._json('/api/pair/state?'+urlencode({'device_id':identity.device_id}),
                          agent_secret=identity.agent_secret)
        return bool(result.get('linked',False))

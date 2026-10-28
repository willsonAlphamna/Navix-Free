"""Cloud opt-in boundaries. No network activity or credentials on import."""
from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlsplit


@dataclass(frozen=True)
class CloudSettings:
    """Disabled by default until NavixX Cloud has verified OAuth and pairing."""

    enabled: bool = False
    relay_url: str = ''

    def validate(self):
        if not self.enabled:
            return
        parsed = urlsplit(self.relay_url)
        if parsed.scheme != 'wss' or not parsed.hostname:
            raise ValueError('O relay NavixX exige URL WebSocket segura (wss://).')
        if parsed.username or parsed.password or parsed.fragment or parsed.query:
            raise ValueError('Relay não aceita senha, token ou parâmetros na URL.')
        host = parsed.hostname.lower()
        if host in {'localhost', '127.0.0.1', '::1'}:
            raise ValueError('Relay público não pode usar endereço local.')
        try:
            addr = ip_address(host)
        except ValueError:
            pass
        else:
            if not addr.is_global:
                raise ValueError('Relay exige endpoint público HTTPS/WSS.')
        if parsed.path not in ('', '/', '/api/device/connect'):
            raise ValueError('Caminho do relay não reconhecido.')


def permission_for_tool(name):
    """Preserve the 44 tool names without trusting remote capability claims."""
    if name == 'status':
        return None
    for prefix, permission in (
        ('browser_', 'browser'), ('desktop_', 'desktop'),
        ('files_', 'files'), ('command_', 'commands'),
    ):
        if isinstance(name, str) and name.startswith(prefix):
            return permission
    raise PermissionError('Ferramenta MCP desconhecida.')


def authorize_cloud_tool(session, name):
    """Enforce the owner's current local session even after cloud OAuth."""
    capability = permission_for_tool(name)
    state = session.status()
    if not state['active']:
        raise PermissionError('Acesso remoto desligado no Windows.')
    if capability is not None:
        session.require(capability)
    return True

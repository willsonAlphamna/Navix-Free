"""Optional NavixX Cloud device-side transport; no network on import.

The Windows owner must authorize a local session and sign in with an OIDC
provider before this client is started. It never reads OpenAI API keys.
"""
import asyncio
import inspect
import json
import re
import time
from urllib.parse import urlencode, urlsplit, urlunsplit

from .cloud import authorize_cloud_tool

_DEVICE = re.compile(r'^[A-Za-z0-9_-]{16,128}$')
_CALL_ID = re.compile(r'^[0-9a-f-]{36}$', re.I)
_TOOLS = frozenset("""
browser_back browser_click browser_close_tab browser_download browser_fill
browser_forward browser_hover browser_navigate browser_open browser_press
browser_read browser_reload browser_screenshot browser_scroll browser_select
browser_snapshot browser_start browser_tabs browser_upload browser_wait
command_exec command_run desktop_click desktop_drag desktop_hotkey desktop_key
desktop_move desktop_position desktop_screen_info desktop_screenshot desktop_scroll
desktop_type files_copy files_delete files_download files_edit files_list
files_mkdir files_move files_read files_read_binary files_write files_write_binary status
""".split())


def device_url(settings, device_id):
    settings.validate()
    if not settings.enabled:
        raise ValueError('Conexão cloud desligada pelo proprietário.')
    if not isinstance(device_id, str) or not _DEVICE.fullmatch(device_id):
        raise ValueError('Identificador de dispositivo inválido.')
    url = urlsplit(settings.relay_url)
    if url.path not in ('', '/', '/api/device/connect'):
        raise ValueError('Endpoint não reconhecido.')
    return urlunsplit(('wss', url.netloc, '/api/device/connect',
                       urlencode({'device_id': device_id}), ''))


class CloudRequestHandler:
    """Handles bounded RPC frames, rechecking live Windows permissions each time."""

    def __init__(self, session, invoke=None, clock=time.time):
        self.session = session
        self.invoke = invoke
        self.clock = clock

    async def handle(self, frame):
        call_id = ''
        try:
            if not isinstance(frame, str) or len(frame.encode('utf-8')) > 8*1024*1024:
                raise ValueError('Mensagem inválida ou grande demais.')
            request = json.loads(frame)
            if not isinstance(request, dict):
                raise ValueError('Formato inválido.')
            call_id = request.get('id', '')
            tool = request.get('tool')
            args = request.get('args')
            deadline = request.get('deadline')
            if (request.get('kind') != 'call' or
                    not isinstance(call_id, str) or not _CALL_ID.fullmatch(call_id) or
                    tool not in _TOOLS or not isinstance(args, dict) or
                    not isinstance(deadline, (int, float)) or
                    isinstance(deadline, bool) or
                    not self.clock()*1000 < deadline <= self.clock()*1000+60000):
                raise ValueError('Chamada não autorizada ou expirada.')
            authorize_cloud_tool(self.session, tool)
            if tool == 'status':
                result = self.session.status()
            else:
                if self.invoke is None:
                    raise PermissionError('Ferramentas remotas ainda não ativadas neste dispositivo.')
                result = self.invoke(tool, args)
                if inspect.isawaitable(result):
                    result = await result
            return json.dumps({'kind': 'result', 'id': call_id, 'ok': True,
                               'result': result}, ensure_ascii=False)
        except Exception:
            # Never leak paths, secrets, stack traces, or exception strings over the relay.
            return json.dumps({'kind': 'result',
                               'id': call_id if isinstance(call_id, str) and _CALL_ID.fullmatch(call_id) else
                                     '00000000-0000-0000-0000-000000000000',
                               'ok': False, 'error': 'Operação recusada ou indisponível.'})


async def connect_once(settings, device_id, get_agent_secret, handler, websocket_connect=None):
    """Connect only with device-specific random secret; no runtime/API key creation."""
    if websocket_connect is None:
        from websockets.asyncio.client import connect as websocket_connect
    endpoint = device_url(settings, device_id)
    token = get_agent_secret()
    if inspect.isawaitable(token):
        token = await token
    if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43,128}', token):
        raise PermissionError('Credencial do dispositivo indisponível.')
    async with websocket_connect(endpoint, additional_headers={'X-Navix-Agent-Token': token},
                                 max_size=12*1024*1024, open_timeout=15, ping_interval=20) as ws:
        async for frame in ws:
            await ws.send(await handler.handle(frame))


async def run_until_stopped(settings, device_id, get_agent_secret, handler, stop_event,
                            connect=connect_once):
    """Stop cancels the LIVE WebSocket immediately, not only the retry delay."""
    delay=1
    while not stop_event.is_set():
        if not handler.session.status().get('active', False):
            return
        task=asyncio.create_task(connect(settings,device_id,get_agent_secret,handler))
        stopped=asyncio.create_task(stop_event.wait())
        try:
            done,_=await asyncio.wait({task,stopped},return_when=asyncio.FIRST_COMPLETED)
            if stopped in done:
                task.cancel()
                await asyncio.gather(task,return_exceptions=True)
                return
            stopped.cancel()
            await asyncio.gather(stopped,return_exceptions=True)
            await task
            delay=1
        except (PermissionError, ValueError):
            return
        except asyncio.CancelledError:
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)
            raise
        except Exception:
            # Transient network failure; no tokens or raw server errors in logs.
            pass
        if stop_event.is_set():
            return
        try:
            await asyncio.wait_for(stop_event.wait(),timeout=delay)
        except asyncio.TimeoutError:
            delay=min(delay*2,60)

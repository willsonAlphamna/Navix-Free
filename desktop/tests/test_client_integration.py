import asyncio
import socket
import time
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from navix.core import Session
from navix.server import Service
from navix.desktop import Desktop


def test_actual_mcp_client_initialize_and_call(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    session = Session(tmp_path)
    service = Service(session, None, Desktop(session), port=port)
    service.start()
    try:
        for _ in range(100):
            if service.server.started: break
            time.sleep(.02)
        assert service.server.started
        async def check():
            async with httpx.AsyncClient(trust_env=False, headers={'Authorization': 'Bearer ' + session.token}) as http:
                async with streamable_http_client('http://127.0.0.1:%d/mcp' % port, http_client=http) as (read, write, _):
                    async with ClientSession(read, write) as client:
                        initialized = await client.initialize()
                        assert initialized.serverInfo.name == 'Navix Desktop'
                        tools = await client.list_tools()
                        names = {tool.name for tool in tools.tools}
                        assert {'files_edit', 'command_run', 'browser_upload', 'desktop_move'} <= names
                        result = await client.call_tool('status', {})
                        assert not result.isError
                        assert 'false' in result.content[0].text.lower()
                        # Exercise real file and subprocess backends through MCP,
                        # not just tool discovery or a fake adapter.
                        session.activate(['files', 'commands'])
                        path = str(tmp_path / 'mcp-test.txt')
                        created = await client.call_tool('files_write', {'path': path, 'text': 'ação'})
                        assert not created.isError
                        edited = await client.call_tool('files_edit', {'path': path,
                            'old_text': 'ação', 'new_text': 'MCP_REAL_OK'})
                        assert not edited.isError
                        read_file = await client.call_tool('files_read', {'path': path})
                        assert not read_file.isError
                        assert 'MCP_REAL_OK' in read_file.content[0].text
                        command = await client.call_tool('command_run', {
                            'shell': 'python', 'command': 'print("COMMAND_MCP_REAL_OK")'})
                        assert not command.isError
                        assert 'COMMAND_MCP_REAL_OK' in command.content[0].text
                        deleted = await client.call_tool('files_delete', {'path': path})
                        assert not deleted.isError
                        assert not (tmp_path / 'mcp-test.txt').exists()
        asyncio.run(check())
    finally:
        service.close()


def test_automatic_port_and_release(tmp_path):
    session = Session(tmp_path)
    service = Service(session, None, Desktop(session), port=0)
    assert service.port > 0
    service.start()
    try:
        for _ in range(100):
            if service.ready: break
            time.sleep(.02)
        assert service.ready
        with httpx.Client(trust_env=False) as client:
            response = client.get('http://127.0.0.1:%d/health' % service.port,
                                  headers={'Authorization': 'Bearer ' + session.token})
        assert response.json()['service'] == 'navix-desktop'
    finally:
        service.close()
    assert not service.ready

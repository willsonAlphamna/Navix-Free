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
                        assert len(tools.tools) == 13
                        result = await client.call_tool('status', {})
                        assert not result.isError
                        assert 'false' in result.content[0].text.lower()
        asyncio.run(check())
    finally:
        service.close()

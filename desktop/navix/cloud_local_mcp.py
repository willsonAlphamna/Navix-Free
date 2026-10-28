"""Bounded bridge into the existing localhost FastMCP server (no public port).

The Windows session token stays on the PC. The Cloud relay sees only the
result of explicitly authorized MCP tool calls.
"""
import asyncio
import json
import uuid
from urllib import request as urlrequest

from .cloud import authorize_cloud_tool, permission_for_tool


class LocalMCPInvoker:
    def __init__(self, session, service, opener=None):
        self.session=session
        self.service=service
        self.opener=opener or urlrequest.build_opener(urlrequest.ProxyHandler({}))

    def _invoke_sync(self, tool, args):
        authorize_cloud_tool(self.session, tool)
        if permission_for_tool(tool) is not None:
            self.session.require(permission_for_tool(tool))
        port=self.service.port
        if not isinstance(port,int) or not 1<=port<=65535 or not self.service.ready:
            raise PermissionError('Servidor MCP local não está pronto.')
        token=self.session.token
        if not isinstance(token,str) or len(token)<16 or any(c.isspace() for c in token):
            raise PermissionError('Sessão local inválida.')
        request_id=str(uuid.uuid4())
        payload={'jsonrpc':'2.0','id':request_id,'method':'tools/call',
                 'params':{'name':tool,'arguments':args}}
        request=urlrequest.Request(
            'http://127.0.0.1:%d/mcp'%port,
            data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),
            headers={'Authorization':'Bearer '+token,
                     'Accept':'application/json, text/event-stream',
                     'Content-Type':'application/json',
                     'MCP-Protocol-Version':'2025-06-18'},
            method='POST')
        # Client is deliberately stateless; only a bounded JSON MCP response is accepted.
        with self.opener.open(request,timeout=40) as response:
            if 'application/json' not in response.headers.get('content-type',''):
                raise RuntimeError('MCP local não retornou JSON.')
            data=response.read(12*1024*1024+1)
        if len(data)>12*1024*1024: raise RuntimeError('Resultado MCP excede limite.')
        obj=json.loads(data)
        if not isinstance(obj,dict) or obj.get('jsonrpc')!='2.0' or obj.get('id')!=request_id:
            raise RuntimeError('Resposta MCP incompatível.')
        if 'error' in obj: raise RuntimeError('A ferramenta local recusou a operação.')
        if 'result' not in obj:raise RuntimeError('Resultado MCP ausente.')
        return obj['result']

    async def __call__(self, tool, args):
        return await asyncio.to_thread(self._invoke_sync,tool,args)

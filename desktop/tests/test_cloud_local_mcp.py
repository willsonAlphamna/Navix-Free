import io
import json
import unittest
from navix.cloud_local_mcp import LocalMCPInvoker


class Session:
    token='x'*48
    active=True
    permissions=['browser','desktop','files']
    def status(self): return {'active':self.active,'permissions':self.permissions}
    def require(self,scope):
        if scope not in self.permissions:raise PermissionError(scope)


class Service:
    ready=True
    port=40645


class Response:
    headers={'content-type':'application/json; charset=utf-8'}
    def __init__(self,payload):self.content=io.BytesIO(json.dumps(payload).encode())
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,length):return self.content.read(length)


class LocalOpener:
    def __init__(self,invalid=False): self.request=None;self.invalid=invalid
    def open(self,req,timeout):
        self.request=req
        payload=json.loads(req.data)
        return Response({'jsonrpc':'2.0',
                         'id':'not-the-same' if self.invalid else payload['id'],
                         'result':{'content':[{'type':'text','text':'ok'}]}})


class CloudLocalMCPTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session=Session()
        self.service=Service()
        self.opener=LocalOpener()
        self.invoke=LocalMCPInvoker(self.session,self.service,self.opener)

    async def test_invokes_local_fastmcp_without_leaking_token(self):
        result=await self.invoke('browser_tabs',{})
        self.assertEqual(result['content'][0]['text'],'ok')
        req=self.opener.request
        self.assertEqual(req.full_url,'http://127.0.0.1:40645/mcp')
        self.assertNotIn(self.session.token,req.full_url)
        self.assertNotIn(self.session.token,req.data.decode())
        self.assertEqual(req.get_header('Authorization'),'Bearer '+self.session.token)

    async def test_rejects_permission_missing(self):
        with self.assertRaises(PermissionError):
            await self.invoke('command_run',{'command':'dir'})
        self.assertIsNone(self.opener.request)

    async def test_rejects_revoked_session(self):
        self.session.active=False
        with self.assertRaises(PermissionError):
            await self.invoke('browser_tabs',{})
        self.assertIsNone(self.opener.request)

    async def test_only_localhost_server_port(self):
        self.service.port=0
        with self.assertRaises(PermissionError):
            await self.invoke('browser_tabs',{})
        self.assertIsNone(self.opener.request)

    async def test_rejects_mismatched_jsonrpc_id(self):
        self.invoke.opener=LocalOpener(invalid=True)
        with self.assertRaises(RuntimeError):
            await self.invoke('browser_tabs',{})

    async def test_rejects_unknown_tool_before_http(self):
        with self.assertRaises(PermissionError):
            await self.invoke('system_admin',{})
        self.assertIsNone(self.opener.request)


if __name__=='__main__': unittest.main()

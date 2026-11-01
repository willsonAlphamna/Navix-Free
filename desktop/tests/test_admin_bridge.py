import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

# Test transport/lifecycle without requiring Windows DPAPI or the GUI.
def load_module():
    name='bridge_under_test'
    package=types.ModuleType(name);package.__path__=[]
    crypto=types.ModuleType(name+'.tunnel_manager');crypto._dpapi=lambda data,protect:data
    sys.modules[name]=package;sys.modules[name+'.tunnel_manager']=crypto
    spec=importlib.util.spec_from_file_location(name+'.admin_bridge',Path(__file__).parents[1]/'navix'/'admin_bridge.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

mod=load_module()

class Session:
    def __init__(self,path):self.directory=path;self.token='native-session-token';self.active=True
    def status(self):return {'active':self.active,'permissions':['commands','files','browser','desktop'] if self.active else []}

class Response:
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,*args):return json.dumps(self.data).encode()

class BridgeTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_native_port_and_rotated_token(self):
        session=Session(self.path);service=types.SimpleNamespace(port=12345,ready=True)
        bridge=mod.AdminBridge(session,lambda:service);seen=[]
        def opened(req,timeout):seen.append(req);return Response({'jsonrpc':'2.0','id':1,'result':{'tools':[]}})
        bridge.local_opener=types.SimpleNamespace(open=opened)
        bridge._local({'jsonrpc':'2.0','id':1,'method':'tools/list'})
        self.assertEqual(seen[0].full_url,'http://127.0.0.1:12345/mcp')
        self.assertEqual(seen[0].get_header('Authorization'),'Bearer native-session-token')
        service.port=23456;session.token='rotated'
        bridge._local({'jsonrpc':'2.0','id':1,'method':'tools/list'})
        self.assertEqual(seen[1].full_url,'http://127.0.0.1:23456/mcp')
        self.assertEqual(seen[1].get_header('Authorization'),'Bearer rotated')
    def test_stop_resume_lifecycle(self):
        bridge=mod.AdminBridge(Session(self.path),lambda:types.SimpleNamespace(port=1,ready=True))
        def loop():
            while not bridge.halt.wait(.01):pass
        bridge._run=loop;bridge.start();thread=bridge.thread
        bridge.stop();self.assertFalse(bridge.enabled.is_set())
        bridge.start();self.assertIs(bridge.thread,thread);self.assertTrue(bridge.enabled.is_set())
        bridge.close();thread.join(1);self.assertFalse(thread.is_alive())
    def test_enrollment_keeps_secrets_out_of_logs(self):
        messages=[];bridge=mod.AdminBridge(Session(self.path),lambda:None,messages.append)
        bridge._cloud=lambda *args:{'device_id':'dev','agent_token':'PRIVATE_TOKEN','setup_url':'https://bridge/setup#ONE_TIME_SECRET'}
        calls=[]
        with patch.object(mod.webbrowser,'open',calls.append):bridge._enroll()
        saved=json.loads(bridge.secret.read_bytes())
        self.assertEqual(saved,{'device_id':'dev','agent_token':'PRIVATE_TOKEN'})
        self.assertNotIn('ONE_TIME_SECRET',bridge.secret.read_text())
        self.assertNotIn('PRIVATE_TOKEN',''.join(messages))
        self.assertEqual(calls,['https://bridge/setup#ONE_TIME_SECRET'])

if __name__=='__main__':unittest.main()

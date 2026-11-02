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

    def test_successful_idle_poll_waits_to_prevent_429(self):
        session=Session(self.path)
        bridge=mod.AdminBridge(session,lambda:types.SimpleNamespace(port=1,ready=True))
        bridge.enabled.set()
        bridge.credentials={'device_id':'abc','agent_token':'secret'}
        bridge.tools=[{'name':'status'}]
        calls=[]
        bridge._cloud=lambda path,data:calls.append(path) or {}

        class StopAfterWait:
            def __init__(self):self.stopped=False;self.waits=[]
            def is_set(self):return self.stopped
            def wait(self,seconds):self.waits.append(seconds);self.stopped=True;return True

        bridge.halt=StopAfterWait()
        bridge._run()
        self.assertEqual(calls,['/device/poll'])
        self.assertEqual(bridge.halt.waits,[10])

    def test_retry_after_429_and_exponential_jitter(self):
        from urllib.error import HTTPError
        with patch.object(mod.random,'uniform',return_value=0):
            err=HTTPError('https://cloud',429,'Rate limited',{'Retry-After':'90'},None)
            self.assertEqual(mod.AdminBridge._retry_delay(5,err),90)
            self.assertEqual(mod.AdminBridge._retry_delay(5),10)
            self.assertEqual(mod.AdminBridge._retry_delay(100),120)

    def test_persist_result_without_reexecuting_remote_job(self):
        credentials={'device_id':'abc','agent_token':'secret'}
        bridge=mod.AdminBridge(Session(self.path),lambda:None)
        bridge.secret.write_bytes(json.dumps(credentials).encode())
        bridge.credentials=credentials
        expected={'job_id':'job:abc:123','result':{'content':[{'type':'text','text':'ok'}]}}
        bridge.pending_result=expected
        bridge._persist_pending()

        recovered=mod.AdminBridge(Session(self.path),lambda:None)
        recovered._load()
        self.assertEqual(recovered.pending_result,expected)
        self.assertTrue(recovered.pending_file.exists())
        recovered._clear_pending()
        self.assertIsNone(recovered.pending_result)
        self.assertFalse(recovered.pending_file.exists())

    def test_pending_result_from_another_device_is_not_adopted(self):
        credentials={'device_id':'abc','agent_token':'secret'}
        bridge=mod.AdminBridge(Session(self.path),lambda:None)
        bridge.secret.write_bytes(json.dumps(credentials).encode())
        payload={'device_id':'other','pending':{'job_id':'job:other:x','result':{}}}
        bridge.pending_file.write_bytes(json.dumps(payload).encode())
        bridge._load()
        self.assertIsNone(bridge.pending_result)
        self.assertTrue(bridge.pending_file.exists())

if __name__=='__main__':unittest.main()

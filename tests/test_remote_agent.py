import pathlib,tempfile,threading,unittest,urllib.request,urllib.error,json
from aegis_core.remote_agent import RemoteAgent
from aegis_core.engine import Audit
class RemoteAgentTests(unittest.TestCase):
 def test_nonlocal_denied(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):RemoteAgent(("0.0.0.0",0),"A"*40,d,Audit(pathlib.Path(d,"a")))
 def test_weak_secret_denied(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):RemoteAgent(("127.0.0.1",0),"short",d,Audit(pathlib.Path(d,"a")))
 def test_endpoints_and_security(self):
  with tempfile.TemporaryDirectory() as d:
   pathlib.Path(d,"file.txt").write_text("safe")
   server=RemoteAgent(("127.0.0.1",0),"A"*40,d,Audit(pathlib.Path(d,"a")))
   thread=threading.Thread(target=server.serve_forever,daemon=True)
   thread.start()
   root="http://127.0.0.1:"+str(server.server_port)
   try:
    with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(root+"/v1/health",timeout=5)
    self.assertEqual(err.exception.code,401)
    def get(path):
     with urllib.request.urlopen(urllib.request.Request(root+path,headers={"Authorization":"Bearer "+"A"*40}),timeout=5) as r:return json.load(r)
    self.assertTrue(get("/v1/health")["online"])
    self.assertIn("cpu_logical",get("/v1/diagnostics"))
    self.assertIn("running",get("/v1/guardian"))
    self.assertTrue(any(x["path"]=="file.txt" for x in get("/v1/files")["files"]))
    with self.assertRaises(urllib.error.HTTPError) as err:
     urllib.request.urlopen(urllib.request.Request(root+"/v1/health",data=b"{}",headers={"Authorization":"Bearer "+"A"*40}),timeout=5)
    self.assertEqual(err.exception.code,405)
   finally:server.shutdown();server.server_close();thread.join(timeout=5)

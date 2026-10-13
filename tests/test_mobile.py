import pathlib,tempfile,threading,unittest,urllib.request,urllib.error,json
from aegis_mobile import MobileServer
from aegis_core.engine import Audit
class MobileTests(unittest.TestCase):
 def test_private_binding(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):MobileServer(("0.0.0.0",0),"Z"*40,d,Audit(pathlib.Path(d,"audit")))
 def test_mobile_page_and_api(self):
  with tempfile.TemporaryDirectory() as d:
   s=MobileServer(("127.0.0.1",0),"Z"*40,d,Audit(pathlib.Path(d,"audit")))
   t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
   url="http://127.0.0.1:"+str(s.server_port)
   try:
    with urllib.request.urlopen(url+"/",timeout=3) as r:
     self.assertIn(b"AEGIS Mobile",r.read())
    with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(url+"/v1/health",timeout=3)
    self.assertEqual(error.exception.code,401)
    request=urllib.request.Request(url+"/v1/health",headers={"Authorization":"Bearer "+"Z"*40})
    with urllib.request.urlopen(request,timeout=3) as r:self.assertTrue(json.load(r)["online"])
   finally:s.shutdown();s.server_close();t.join(timeout=5)

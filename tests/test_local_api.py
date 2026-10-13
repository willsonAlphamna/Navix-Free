import pathlib,tempfile,threading,unittest,urllib.request,urllib.error,json
from aegis_local_api import ControlServer
from aegis_core.engine import Audit
class LocalApiTests(unittest.TestCase):
    def test_reject_external_bind(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):ControlServer(("0.0.0.0",0),"X"*40,d,Audit(pathlib.Path(d,"audit")))
    def test_auth_and_health(self):
        with tempfile.TemporaryDirectory() as d:
            s=ControlServer(("127.0.0.1",0),"X"*40,d,Audit(pathlib.Path(d,"audit")))
            t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            url=f"http://127.0.0.1:{s.server_address[1]}/health"
            try:
                with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(url,timeout=3)
                self.assertEqual(e.exception.code,401)
                request=urllib.request.Request(url,headers={"Authorization":"Bearer "+"X"*40})
                with urllib.request.urlopen(request,timeout=3) as r:
                    self.assertEqual(json.load(r)["status"],"ok")
            finally:s.shutdown();s.server_close();t.join(timeout=3)

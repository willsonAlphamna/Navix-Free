import tempfile, unittest, json, pathlib
from aegis_core.engine import Workspace, Audit, Engine, diagnostic, run_diagnostic
from aegis_core.browser import BrowserController
from aegis_core.approvals import Approvals

class CoreTests(unittest.TestCase):
    def test_workspace_escape(self):
        with tempfile.TemporaryDirectory() as d:
            ws=Workspace(d)
            with self.assertRaises(PermissionError):ws.resolve("../escape")
    def test_hash(self):
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d,"x.txt").write_bytes(b"abc")
            self.assertEqual(Workspace(d).hash_file("x.txt"),"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    def test_copy_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d,"x").write_text("hello")
            ws=Workspace(d);ws.copy_safe("x","y")
            self.assertEqual(pathlib.Path(d,"y").read_text(),"hello")
            with self.assertRaises(FileExistsError):ws.copy_safe("x","y")
    def test_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d,"x").write_text("data")
            self.assertEqual(len(Workspace(d).inventory()),1)
    def test_engine(self):
        with tempfile.TemporaryDirectory() as d:
            audit=Audit(pathlib.Path(d,"audit.jsonl"))
            engine=Engine(Workspace(d),audit)
            ident,future=engine.submit("test",lambda:3)
            future.result(timeout=5)
            self.assertEqual(engine.status(ident)["state"],"completed")
            engine.shutdown()
    def test_audit(self):
        with tempfile.TemporaryDirectory() as d:
            a=Audit(pathlib.Path(d,"a.jsonl"));a.add("test","ok")
            self.assertEqual(json.loads(pathlib.Path(d,"a.jsonl").read_text())["status"],"ok")
    def test_diagnostic(self):self.assertIn("cpu_logical",diagnostic())
    def test_reject_command(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError):run_diagnostic("cmd /c del",Audit(pathlib.Path(d,"a.jsonl")))
    def test_approval(self):
        a=Approvals();ticket=a.request("backup","test")
        with self.assertRaises(PermissionError):a.consume(ticket,"backup","test")
        ticket=a.request("backup","test");a.approve(ticket,"backup","test")
        self.assertTrue(a.consume(ticket,"backup","test"))
        with self.assertRaises(PermissionError):a.consume(ticket,"backup","test")
    def test_browser_allowlist(self):
        b=BrowserController({"example.com"})
        self.assertEqual(b.validate("https://example.com/path"),"https://example.com/path")
        for url in ("http://example.com","https://evil.example.com","file:///etc/passwd"):
            with self.assertRaises(PermissionError):b.validate(url)

if __name__=="__main__":unittest.main()

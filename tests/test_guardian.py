import pathlib,tempfile,unittest
from aegis_core.engine import Audit
from aegis_core.guardian import Guardian

class GuardianTests(unittest.TestCase):
    def setup_guardian(self, path):
        return Guardian(path,Audit(pathlib.Path(path,"audit.jsonl")),interval=1)
    def test_blocks_privileged_action(self):
        with tempfile.TemporaryDirectory() as d:
            g=self.setup_guardian(d)
            allowed,finding=g.evaluate_action("delete","some.txt")
            self.assertFalse(allowed)
            self.assertEqual(finding.code,"approval_required")
    def test_allows_approved_action(self):
        with tempfile.TemporaryDirectory() as d:
            g=self.setup_guardian(d)
            self.assertTrue(g.evaluate_action("delete","some.txt",approved=True)[0])
    def test_blocks_unknown_action(self):
        with tempfile.TemporaryDirectory() as d:
            g=self.setup_guardian(d)
            self.assertFalse(g.evaluate_action("unknown-verb","x")[0])
    def test_detects_file_change(self):
        with tempfile.TemporaryDirectory() as d:
            g=self.setup_guardian(d)
            f=pathlib.Path(d,"sample.txt")
            f.write_text("a")
            g.check_once()
            f.write_text("much longer")
            result=g.check_once()
            self.assertTrue(any(x.subject=="sample.txt" and x.code=="changed" for x in result))
    def test_detects_removal(self):
        with tempfile.TemporaryDirectory() as d:
            g=self.setup_guardian(d)
            f=pathlib.Path(d,"sample.txt");f.write_text("a")
            g.check_once();f.unlink()
            self.assertIn("removed",[x.code for x in g.check_once()])
    def test_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            g=self.setup_guardian(d)
            self.assertTrue(g.start())
            self.assertFalse(g.start())
            g.stop()
            self.assertFalse(g.status()["running"])
    def test_interval(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):Guardian(d,Audit(pathlib.Path(d,"log")),interval=0)

import pathlib, tempfile, io, contextlib, json, unittest
from aegis_cli import main
class CLITests(unittest.TestCase):
    def test_inventory_command(self):
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d,"a.txt").write_text("ok")
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                code=main(["--workspace",d,"--audit",str(pathlib.Path(d,"audit.jsonl")),"inventory"])
            self.assertEqual(code,0)
            self.assertTrue(any(x["path"]=="a.txt" for x in json.loads(output.getvalue())))
    def test_path_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                code=main(["--workspace",d,"--audit",str(pathlib.Path(d,"audit.jsonl")),"sha256","../escape"])
            self.assertEqual(code,1)
            self.assertIn("error",json.loads(output.getvalue()))
    def test_system_command(self):
        with tempfile.TemporaryDirectory() as d:
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                code=main(["--audit",str(pathlib.Path(d,"audit.jsonl")),"system"])
            self.assertEqual(code,0)
            self.assertIn("cpu_logical",json.loads(output.getvalue()))

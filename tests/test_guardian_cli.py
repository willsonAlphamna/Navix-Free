import pathlib,tempfile,unittest,io,contextlib,json
from aegis_guardian import main
class GuardianCLITests(unittest.TestCase):
 def test_once(self):
  with tempfile.TemporaryDirectory() as d:
   audit=str(pathlib.Path(d)/"guardian.jsonl")
   output=io.StringIO()
   with contextlib.redirect_stdout(output):
    code=main(["--workspace",d,"--audit",audit,"--once"])
   self.assertEqual(code,0)
   self.assertIn("guardian",json.loads(output.getvalue()))
   self.assertTrue(pathlib.Path(audit).exists())
 def test_bad_interval(self):
  with self.assertRaises(SystemExit):main(["--interval","0","--once"])

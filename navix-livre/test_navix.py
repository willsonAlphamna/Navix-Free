import json
import tempfile
from pathlib import Path
import unittest
from navix_livre import Agent,call,tools

class TestNavix(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.r=Path(self.t.name)
        self.a=Agent(roots=[self.r],write=False,commands=False,ui=False)
    def tearDown(self): self.t.cleanup()
    def test_list_search(self):
        (self.r/"Musicas").mkdir()
        (self.r/"Musicas"/"arquivo.txt").write_text("ola",encoding="utf-8")
        self.assertEqual(self.a.list_directory(str(self.r))["arquivos"][0]["nome"],"Musicas")
        self.assertEqual(len(self.a.search_files(str(self.r),"arquivo")["resultados"]),1)
    def test_escape(self):
        with self.assertRaises(PermissionError): self.a.safe(self.r.parent)
    def test_write(self):
        with self.assertRaises(PermissionError): self.a.write_text(str(self.r/"a.txt"),"ok")
        self.a.write=True
        self.a.write_text(str(self.r/"a.txt"),"ok")
        self.assertEqual(self.a.read_text(str(self.r/"a.txt"))["texto"],"ok")
    def test_privileges(self):
        with self.assertRaises(PermissionError): self.a.run_command("dir")
        with self.assertRaises(PermissionError): self.a.open_url("https://example.org")
        with self.assertRaises(PermissionError): self.a.screenshot()
    def test_mcp(self):
        self.assertEqual(len(tools()),10)
        v=json.loads(call(self.a,"status",{})["content"][0]["text"])
        self.assertEqual(v["nome"],"Navix Livre")
if __name__=="__main__":unittest.main()

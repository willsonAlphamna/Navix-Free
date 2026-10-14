import json
import ast
import tempfile
from pathlib import Path
import unittest
from navix_livre import Agent,call,tools,VERSION
import navix_gui

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
    def test_read_binary_rejected(self):
        p=self.r/"picture.dat"
        p.write_bytes(b"abc"+bytes([0])+b"def")
        with self.assertRaises(ValueError): self.a.read_text(str(p))

    def test_large_file_rejected(self):
        p=self.r/"big.txt"
        p.write_bytes(b"a"*1_000_001)
        with self.assertRaises(ValueError): self.a.read_text(str(p))

    def test_listing_truncated_flag(self):
        for i in range(502): (self.r/("n"+str(i))).touch()
        result=self.a.list_directory(str(self.r))
        self.assertTrue(result["truncado"])
        self.assertEqual(len(result["arquivos"]),500)

    def test_escape(self):
        with self.assertRaises(PermissionError): self.a.safe(self.r.parent)
    def test_write(self):
        with self.assertRaises(PermissionError): self.a.write_text(str(self.r/"a.txt"),"ok")
        self.a.write=True
        self.a.write_text(str(self.r/"a.txt"),"ok")
        self.assertEqual(self.a.read_text(str(self.r/"a.txt"))["texto"],"ok")
    def test_metadata_and_write_ops(self):
        original=self.r/"original.txt"
        original.write_text("ok",encoding="utf-8")
        info=self.a.get_file_info(str(original))
        self.assertEqual(info["nome"],"original.txt")
        self.assertEqual(info["tamanho_bytes"],2)
        with self.assertRaises(PermissionError):
            self.a.create_directory(str(self.r/"Pasta"))
        with self.assertRaises(PermissionError):
            self.a.move_file(str(original),str(self.r/"renamed.txt"))
        self.a.write=True
        folder=self.r/"Pasta"
        self.a.create_directory(str(folder))
        target=folder/"renamed.txt"
        self.a.move_file(str(original),str(target))
        self.assertFalse(original.exists())
        self.assertEqual(target.read_text(encoding="utf-8"),"ok")
        with self.assertRaises(FileExistsError):
            self.a.create_directory(str(folder))
        with self.assertRaises(ValueError):
            self.a.move_file(str(folder),str(folder/"filho"))

    def test_privileges(self):
        with self.assertRaises(PermissionError): self.a.run_command("dir")
        with self.assertRaises(PermissionError): self.a.open_url("https://example.org")
        with self.assertRaises(PermissionError): self.a.screenshot()
    def test_modern_gui_code(self):
        path=Path(navix_gui.__file__)
        ast.parse(path.read_text(encoding='utf-8'))
        self.assertRegex(VERSION,r'^\d+\.\d+\.\d+$')
        for method in ('build_files','build_terminal','build_processes','build_capture','build_settings','start_bridge'):
            self.assertTrue(callable(getattr(navix_gui.NavixWindow,method)))
    def test_mcp(self):
        self.assertEqual(len(tools()),14)
        v=json.loads(call(self.a,"status",{})["content"][0]["text"])
        self.assertEqual(v["nome"],"Navix Livre")
if __name__=="__main__":unittest.main()

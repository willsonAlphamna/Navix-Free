"""Testes locais da ponte HTTP MCP com autenticação."""
import http.client
from http.server import HTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest

from navix_livre import Agent
from navix_remote import load_token, make_handler

class TestBridge(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.home=Path(self.directory.name)
        (self.home/"Musicas").mkdir()
        self.token=load_token(self.home/"bridge.token")
        self.agent=Agent(roots=[self.home],write=False,commands=False,ui=False)
        self.server=HTTPServer(("127.0.0.1",0),make_handler(self.agent,self.token))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.directory.cleanup()

    def query(self,token=None,method="POST",body=None,path="/mcp"):
        conn=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=4)
        payload=body if body is not None else {"jsonrpc":"2.0","id":1,"method":"tools/list"}
        headers={"Content-Type":"application/json"}
        if token is not None:
            headers["Authorization"]="Bearer "+token
        conn.request(method,path,json.dumps(payload) if method=="POST" else None,headers)
        response=conn.getresponse()
        code=response.status
        data=response.read()
        conn.close()
        return code,json.loads(data) if data else None

    def test_denied_without_token(self):
        self.assertEqual(self.query()[0],401)
        self.assertEqual(self.query("wrong")[0],401)

    def test_defaults_are_read_only(self):
        code,payload=self.query(self.token)
        self.assertEqual(code,200)
        names={item["name"] for item in payload["result"]["tools"]}
        self.assertIn("list_directory",names)
        self.assertIn("get_file_info",names)
        self.assertIn("list_processes",names)
        self.assertNotIn("create_directory",names)
        self.assertNotIn("move_file",names)
        self.assertNotIn("run_command",names)
        self.assertNotIn("write_text",names)
        self.assertNotIn("click",names)
        self.assertNotIn("type_text",names)
        self.assertNotIn("drag_mouse",names)

    def test_directory_tool(self):
        request={"jsonrpc":"2.0","id":4,"method":"tools/call",
                 "params":{"name":"list_directory","arguments":{"path":str(self.home)}}}
        code,payload=self.query(self.token,body=request)
        self.assertEqual(code,200)
        self.assertIn("Musicas",payload["result"]["content"][0]["text"])

    def test_disallowed_terminal(self):
        request={"jsonrpc":"2.0","id":3,"method":"tools/call",
                 "params":{"name":"run_command","arguments":{"command":"dir"}}}
        _,payload=self.query(self.token,body=request)
        self.assertTrue(payload["result"]["isError"])

    def test_initialize_and_health(self):
        req={"jsonrpc":"2.0","id":5,"method":"initialize",
             "params":{"protocolVersion":"2025-03-26"}}
        code,payload=self.query(self.token,body=req)
        self.assertEqual(code,200)
        self.assertEqual(payload["result"]["serverInfo"]["name"],"navix-livre")
        self.assertEqual(self.query(self.token,method="GET",path="/health")[0],200)
        self.assertEqual(self.query(method="GET",path="/health")[0],401)

    def test_get_mcp_returns_405_without_sse(self):
        code,payload=self.query(self.token,method="GET",path="/mcp")
        self.assertEqual(code,405)
        self.assertIn("error",payload)

    def test_invalid_json_rpc_method(self):
        code,payload=self.query(self.token,body={"jsonrpc":"2.0","id":7,"method":None})
        self.assertEqual(code,400)
        self.assertIn("error",payload)

    def test_forbidden_origin_and_host(self):
        conn=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=4)
        payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/list"})
        conn.request("POST","/mcp",payload,{
            "Content-Type":"application/json",
            "Authorization":"Bearer "+self.token,
            "Origin":"https://example.org"})
        result=conn.getresponse()
        self.assertEqual(result.status,403)
        result.read()
        conn.close()
        conn=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=4)
        conn.putrequest("POST","/mcp",skip_host=True)
        conn.putheader("Host","outside.example")
        conn.putheader("Content-Type","application/json")
        conn.putheader("Authorization","Bearer "+self.token)
        conn.putheader("Content-Length",str(len(payload.encode("utf-8"))))
        conn.endheaders(payload.encode("utf-8"))
        response=conn.getresponse()
        self.assertEqual(response.status,403)
        response.read()
        conn.close()

    def test_notification(self):
        req={"jsonrpc":"2.0","method":"notifications/initialized"}
        self.assertEqual(self.query(self.token,body=req)[0],202)

if __name__=="__main__":
    unittest.main()

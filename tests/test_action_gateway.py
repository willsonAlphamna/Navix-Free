import tempfile,pathlib,threading,urllib.request,urllib.error,json,unittest
from aegis_action_gateway import Gateway
from aegis_core.engine import Audit
class FakeDesktop:
 def __init__(self):self.events=[]
 def move(self,x,y):self.events.append(("move",x,y))
 def click(self,x,y):self.events.append(("click",x,y))
 def scroll(self,s):self.events.append(("scroll",s))
 def type_text(self,t):self.events.append(("text",t))
class GatewayTests(unittest.TestCase):
 def test_approval_and_actions(self):
  with tempfile.TemporaryDirectory() as d:
   desk=FakeDesktop();s=Gateway(("127.0.0.1",0),"a"*48,Audit(pathlib.Path(d,"audit")),desk)
   t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
   endpoint="http://127.0.0.1:"+str(s.server_port)+"/action"
   def send(token,op):
    req=urllib.request.Request(endpoint,data=json.dumps(op).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
     with urllib.request.urlopen(req,timeout=3) as r:return r.status
    except urllib.error.HTTPError as e:return e.code
   try:
    self.assertEqual(send("wrong",{"op":"click","x":10,"y":20}),401)
    self.assertEqual(send("a"*48,{"op":"click","x":10,"y":20}),403)
    s.allow_session(10)
    self.assertEqual(send("a"*48,{"op":"click","x":10,"y":20}),200)
    self.assertEqual(send("a"*48,{"op":"text","value":"teste"}),200)
    self.assertEqual(send("a"*48,{"op":"scroll","steps":-2}),200)
    self.assertEqual(desk.events,[("click",10,20),("text","teste"),("scroll",-2)])
    s.revoke();self.assertEqual(send("a"*48,{"op":"click","x":10,"y":20}),403)
   finally:s.shutdown();s.server_close();t.join(timeout=3)
 def test_external_bind_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):Gateway(("0.0.0.0",0),"a"*48,Audit(pathlib.Path(d,"audit")),FakeDesktop())

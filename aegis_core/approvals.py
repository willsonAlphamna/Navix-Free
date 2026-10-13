"""One-operation authorization. This module does not bypass OS authorization."""
import secrets, time, threading

class Approvals:
    def __init__(self,ttl_seconds=90):
        self.ttl=ttl_seconds
        self.pending={}
        self.lock=threading.Lock()
    def request(self,action,subject):
        ticket=secrets.token_urlsafe(24)
        with self.lock:self.pending[ticket]={"action":action,"subject":subject,"expiry":time.monotonic()+self.ttl,"approved":False}
        return ticket
    def approve(self,ticket,action,subject):
        with self.lock:
            item=self.pending.get(ticket)
            if not item or item["action"]!=action or item["subject"]!=subject or time.monotonic()>item["expiry"]:
                raise PermissionError("Invalid or expired approval")
            item["approved"]=True
    def consume(self,ticket,action,subject):
        with self.lock:
            item=self.pending.pop(ticket,None)
            if not item or not item["approved"] or item["action"]!=action or item["subject"]!=subject or time.monotonic()>item["expiry"]:
                raise PermissionError("Missing approval")
            return True

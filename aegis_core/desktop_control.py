"""Windows local desktop actions; invoke only after one-time approval.
These primitives do not themselves open network ports or bypass consent.
"""
import ctypes,os
from ctypes import wintypes
ULONG_PTR=ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p)==8 else ctypes.c_ulong
class KEYBDINPUT(ctypes.Structure):
 _fields_=[("wVk",wintypes.WORD),("wScan",wintypes.WORD),("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ULONG_PTR)]
class MOUSEINPUT(ctypes.Structure):
 _fields_=[("dx",wintypes.LONG),("dy",wintypes.LONG),("mouseData",wintypes.DWORD),("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ULONG_PTR)]
class HARDWAREINPUT(ctypes.Structure):
 _fields_=[("uMsg",wintypes.DWORD),("wParamL",wintypes.WORD),("wParamH",wintypes.WORD)]
class INPUTUNION(ctypes.Union):
 _fields_=[("ki",KEYBDINPUT),("mi",MOUSEINPUT),("hi",HARDWAREINPUT)]
class INPUT(ctypes.Structure):
 _fields_=[("type",wintypes.DWORD),("data",INPUTUNION)]
class DesktopControl:
 def __init__(self):
  if os.name!="nt":raise OSError("Windows only")
  self.u=ctypes.windll.user32
  self.u.SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(INPUT),ctypes.c_int]
  self.u.SendInput.restype=wintypes.UINT
 def size(self):return self.u.GetSystemMetrics(0),self.u.GetSystemMetrics(1)
 def point(self,x,y):
  w,h=self.size();x=int(x);y=int(y)
  if not 0<=x<w or not 0<=y<h:raise ValueError("Coordinates outside screen")
  return x,y
 def send(self,events):
  array=(INPUT*len(events))(*events)
  if self.u.SendInput(len(events),array,ctypes.sizeof(INPUT))!=len(events):
   raise OSError("SendInput failed (desktop might be locked or elevated)")
 def move(self,x,y):
  x,y=self.point(x,y)
  if not self.u.SetCursorPos(x,y):raise OSError("SetCursorPos failed")
 def click(self,x,y):
  self.move(x,y)
  self.send([INPUT(type=0,data=INPUTUNION(mi=MOUSEINPUT(dwFlags=2))),INPUT(type=0,data=INPUTUNION(mi=MOUSEINPUT(dwFlags=4)))])
 def scroll(self,steps):
  steps=int(steps)
  if not -10<=steps<=10:raise ValueError("Scroll out of range")
  self.send([INPUT(type=0,data=INPUTUNION(mi=MOUSEINPUT(mouseData=(steps*120)&0xffffffff,dwFlags=0x800)))])
 def type_text(self,text):
  if not isinstance(text,str) or len(text)>500:raise ValueError("Text too long")
  events=[]
  for char in text:
   code=ord(char)
   if 0xD800<=code<=0xDFFF:raise ValueError("Invalid surrogate")
   units=[code] if code<=0xffff else [0xd800+((code-0x10000)>>10),0xdc00+((code-0x10000)&1023)]
   for unit in units:
    events.extend([INPUT(type=1,data=INPUTUNION(ki=KEYBDINPUT(wScan=unit,dwFlags=4))),
                   INPUT(type=1,data=INPUTUNION(ki=KEYBDINPUT(wScan=unit,dwFlags=6)))])
  for i in range(0,len(events),80):self.send(events[i:i+80])

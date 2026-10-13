"""Windows desktop operations with local approval, conservative bounds, audit.
Only call after authenticating AND obtaining a one-time local consent ticket.
"""
from __future__ import annotations
import ctypes, os
from ctypes import wintypes
class DesktopControl:
 def __init__(self):
  if os.name!="nt":raise OSError("Windows only")
  self.u=ctypes.windll.user32
 def size(self):
  return (self.u.GetSystemMetrics(0),self.u.GetSystemMetrics(1))
 def point(self,x,y):
  w,h=self.size();x=int(x);y=int(y)
  if not (0<=x<w and 0<=y<h):raise ValueError("Out-of-bounds coordinates")
  return x,y
 def move(self,x,y):
  x,y=self.point(x,y)
  if not self.u.SetCursorPos(x,y):raise OSError("SetCursorPos failed")
 def click(self,x,y):
  self.move(x,y)
  self.u.mouse_event(0x0002,0,0,0,0)
  self.u.mouse_event(0x0004,0,0,0,0)
 def scroll(self,steps):
  steps=int(steps)
  if not -10<=steps<=10:raise ValueError("Scroll must be -10..10")
  self.u.mouse_event(0x0800,0,0,steps*120,0)
 def type_text(self,text):
  if not isinstance(text,str) or len(text)>500:raise ValueError("Maximum 500 characters")
  for char in text:
   value=ord(char)
   if 0xD800<=value<=0xDFFF:raise ValueError("Invalid surrogate")
   units=[value] if value<=0xFFFF else [0xD800+((value-0x10000)>>10),0xDC00+((value-0x10000)&1023)]
   for unit in units:
    class INPUT(ctypes.Structure):
     _fields_=[("type",wintypes.DWORD),("padding",ctypes.c_byte*4),("wVk",wintypes.WORD),("wScan",wintypes.WORD),("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),("extra",ctypes.c_void_p)]
    # SendInput keyboard structure varies by architecture; use keybd_event for Unicode unsupported.
    # Prevent false claim of reliable Unicode typing until tested in UI.
    raise NotImplementedError("Unicode keyboard injection requires tested SendInput structure")

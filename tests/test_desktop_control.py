import unittest,os
from aegis_core.desktop_control import DesktopControl
class DesktopTests(unittest.TestCase):
 def test_platform_contract(self):
  if os.name!="nt":
   with self.assertRaises(OSError):DesktopControl()
  else:
   d=DesktopControl()
   w,h=d.size()
   self.assertGreater(w,0);self.assertGreater(h,0)
   with self.assertRaises(ValueError):d.point(-1,0)
   with self.assertRaises(ValueError):d.scroll(100)

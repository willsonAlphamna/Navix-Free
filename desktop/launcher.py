"""Entry point shared by source and frozen Windows builds."""
import os
import sys
from pathlib import Path
if getattr(sys, 'frozen', False):
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(Path(sys._MEIPASS) / 'browsers')
def elevate_cloud_admin():
    if '--cloud-admin' not in sys.argv or sys.platform != 'win32':
        return
    import ctypes
    import subprocess
    if ctypes.windll.shell32.IsUserAnAdmin():
        return
    args = sys.argv[1:] if getattr(sys, 'frozen', False) else [str(Path(__file__).resolve()), *sys.argv[1:]]
    result = ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, subprocess.list2cmdline(args), None, 1)
    if result <= 32:
        raise SystemExit('A elevacao de administrador nao foi autorizada pelo Windows.')
    raise SystemExit(0)

if __name__ == '__main__':
    elevate_cloud_admin()
from navix.gui import main
if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from navix.selftest import run
        sys.exit(run(sys.argv[2]))
    main()


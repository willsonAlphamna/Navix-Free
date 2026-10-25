"""Entry point shared by source and frozen Windows builds."""
import os
import sys
from pathlib import Path
if getattr(sys, 'frozen', False):
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(Path(sys._MEIPASS) / 'browsers')
from navix.gui import main
if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from navix.selftest import run
        sys.exit(run(sys.argv[2]))
    main()

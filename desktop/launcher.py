"""Entry point shared by source and frozen Windows builds."""
import os
import sys
from pathlib import Path
if getattr(sys, 'frozen', False):
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(Path(sys._MEIPASS) / 'browsers')
    if (Path(sys.executable).resolve().parent / 'navix-cloud-preview.flag').is_file():
        # Isolate ALL configuration, local authorization, and device credentials
        # from a previous 0.2.11 installation, preserving the original app.
        base = Path(os.environ.get('LOCALAPPDATA', str(Path.home())))
        os.environ['NAVIX_PROFILE_DIR'] = str(base / 'NavixDesktopCloudPreview')
        os.environ['NAVIX_CLOUD_WSS_URL'] = (
            'wss://navixx-cloud-staging.navixx-alfamna.workers.dev/api/device/connect'
        )
from navix.gui import main
if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from navix.selftest import run
        sys.exit(run(sys.argv[2]))
    main()

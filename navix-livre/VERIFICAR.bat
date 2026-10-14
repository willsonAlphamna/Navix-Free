@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 navix_livre.py --doctor
  py -3 -m unittest test_navix -v
) else (
  python navix_livre.py --doctor
  python -m unittest test_navix -v
)
pause

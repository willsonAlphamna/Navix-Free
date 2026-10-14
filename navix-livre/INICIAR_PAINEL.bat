@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (py -3 navix_livre.py --gui) else (python navix_livre.py --gui)
if errorlevel 1 pause

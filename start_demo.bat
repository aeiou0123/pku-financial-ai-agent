@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python scripts\launch_demo.py
) else (
  py -3 scripts\launch_demo.py
)
if errorlevel 1 goto failed
exit /b 0
:failed
echo Startup failed. Check Python installation, internet access and the messages above.
pause
exit /b 1

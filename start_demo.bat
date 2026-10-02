@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python -m venv .venv-demo
) else (
  py -3 -m venv .venv-demo
)
if errorlevel 1 goto failed
".venv-demo\Scripts\python.exe" -m pip install -r requirements-demo.txt
if errorlevel 1 goto failed
".venv-demo\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
if errorlevel 1 goto failed
exit /b 0
:failed
echo Startup failed. Check Python installation, internet access and the messages above.
pause
exit /b 1

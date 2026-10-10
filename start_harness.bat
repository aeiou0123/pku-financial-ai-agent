@echo off
cd /d "%~dp0"
py -3.12 scripts\launch_harness.py
if errorlevel 1 pause

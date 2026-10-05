@echo off
cd /d "%~dp0"
".venv\Scripts\pythonw.exe" desktop.py --data-dir "%~dp0data" --port 8003 %*

@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Eerst installeren volgens LEESMIJ.md.
  pause
  exit /b 1
)
call "%~dp0Start-tool.bat" %*

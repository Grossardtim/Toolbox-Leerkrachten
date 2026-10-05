@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo De Python-omgeving ontbreekt. Volg eerst de installatie in LEESMIJ.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "tools\start_local.py" %*
if errorlevel 1 (
  echo.
  echo Opstarten is niet gelukt. Zie de melding hierboven.
  pause
  exit /b 1
)
endlocal

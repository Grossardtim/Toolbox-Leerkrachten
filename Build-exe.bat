@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" tools\check_build_target.py
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm Leerkrachtenportaal.spec
if errorlevel 1 goto failed
echo.
echo Klaar: dist\LeerkrachtenTool.exe
echo Gebruikersgegevens zijn niet opgenomen in dit bestand.
pause
exit /b 0
:failed
echo.
echo Bouwen is mislukt. Controleer de melding hierboven.
pause
exit /b 1

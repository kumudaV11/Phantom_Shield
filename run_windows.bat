@echo off
cd /d "%~dp0"
echo ==== PHANTOM SHIELD setup ====
set PYCMD=
python --version >nul 2>&1 && set PYCMD=python
if "%PYCMD%"=="" (py -3 --version >nul 2>&1 && set PYCMD=py -3)
if "%PYCMD%"=="" (
  echo ERROR: Python 3 was not found. Install it from https://www.python.org/downloads/
  echo and tick "Add Python to PATH", then run this file again.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PYCMD% -m venv .venv
  if errorlevel 1 ( echo ERROR: could not create the virtual environment. & pause & exit /b 1 )
)
echo Installing dependencies (needs internet the first time only)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 ( echo ERROR: dependency installation failed. Check your internet connection. & pause & exit /b 1 )
echo.
echo PHANTOM SHIELD is starting. Open http://127.0.0.1:5000 in your browser.
echo Press Ctrl+C in this window to stop the server.
start "" http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
pause

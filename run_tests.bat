@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo No virtual environment found. Run run_windows.bat once first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
".venv\Scripts\python.exe" -m pytest -v
pause

@echo off
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3.12 or later from python.org first.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :failed
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :failed
echo Open http://127.0.0.1:5000 in your browser. Press Ctrl+C to stop.
.venv\Scripts\python.exe run.py
pause
exit /b
:failed
echo Setup failed. Check Python and your Internet connection, then try again.
pause
exit /b 1

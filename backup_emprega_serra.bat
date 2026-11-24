@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Execute iniciar_emprega_serra.bat primeiro.
  pause
  exit /b 1
)
"venv\Scripts\python.exe" backup_database.py
pause

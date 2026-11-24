@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo Execute iniciar_emprega_serra.bat primeiro para preparar o ambiente.
    pause
    exit /b 1
)
call "venv\Scripts\activate.bat"
set /p ADMIN_EMAIL=Digite o e-mail do administrador: 
python -m flask --app app create-admin "%ADMIN_EMAIL%"
pause
endlocal

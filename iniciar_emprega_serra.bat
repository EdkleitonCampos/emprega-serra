@echo off
setlocal
cd /d "%~dp0"
set ADMIN_DATABASE_PATH=%CD%\instance\admin_users.sqlite3

echo ==========================================
echo          EMPREGA SERRA - INICIALIZAR
echo ==========================================

if not exist "venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 goto erro
)

call "venv\Scripts\activate.bat"
if errorlevel 1 goto erro

echo Conferindo dependencias...
python -c "import flask, flask_limiter, reportlab, waitress" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias. A primeira instalacao precisa de internet...
    python -m pip install -r requirements.txt
    if errorlevel 1 goto erro
)

echo.
echo Preparando os dados demonstrativos (sem duplicar cadastros)...
python popular_dados_demo.py
if errorlevel 1 goto erro

echo.
echo Sistema iniciando. Acesse http://127.0.0.1:5000
echo Para encerrar, pressione CTRL+C.
python app.py
if errorlevel 1 goto erro

goto fim

:erro
echo.
echo Ocorreu um erro. Confira as mensagens acima.
pause
:fim
endlocal

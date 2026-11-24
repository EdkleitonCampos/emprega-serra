@echo off
setlocal
cd /d "%~dp0"
set ADMIN_DATABASE_PATH=%CD%\instance\admin_users.sqlite3
echo ==========================================
echo EMPREGA SERRA - ACESSO NA REDE WI-FI
echo ==========================================
if not exist "venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  python -m venv venv
  if errorlevel 1 goto erro
)
call "venv\Scripts\activate.bat"
python -c "import flask, flask_limiter, reportlab, waitress" >nul 2>&1
if errorlevel 1 (
  echo Instalando dependencias. A primeira instalacao precisa de internet...
  python -m pip install -r requirements.txt
  if errorlevel 1 goto erro
)
python popular_dados_demo.py
if errorlevel 1 goto erro
echo.
echo Enderecos IPv4 deste computador:
powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254*'} | Select-Object -ExpandProperty IPAddress"
echo.
echo No celular conectado ao MESMO Wi-Fi, abra:
echo http://IP-QUE-APARECE-ACIMA:5000
echo.
echo Este modo funciona somente na mesma rede local.
echo Nao use este modo para publicar na internet.
echo.
set HOST=0.0.0.0
set COOKIE_SECURE=0
set FLASK_DEBUG=0
venv\Scripts\waitress-serve.exe --listen=0.0.0.0:5000 wsgi:app
goto fim
:erro
echo Falha ao preparar ou iniciar o sistema.
pause
:fim
endlocal

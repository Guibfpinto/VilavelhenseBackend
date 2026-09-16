@echo off
title Vilavelhense FC - Instalacao do Backend
setlocal enabledelayedexpansion

set "BACKEND_DIR=%~dp0"
set "BACKEND_DIR=%BACKEND_DIR:~0,-1%"
set "VENV_DIR=%BACKEND_DIR%\venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "REQUIREMENTS=%BACKEND_DIR%\requirements.txt"

echo ============================================================
echo   VILAVELHENSE FC - INSTALACAO DO BACKEND
echo ============================================================
echo.

REM --- Detectar IP ---
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '169.*' -and $_.IPAddress -notlike '127.*' -and $_.InterfaceAlias -notlike '*Loopback*' -and $_.InterfaceAlias -notlike '*Virtual*' } | Sort-Object InterfaceMetric | Select-Object -First 1 -ExpandProperty IPAddress"`) do (
    set "HOST=%%a"
)
if "!HOST!"=="" set "HOST=DESCONHECIDO"
echo 📡 IP do PC: !HOST!
echo.

REM --- Verifica Python ---
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nao encontrado. Instale em https://www.python.org/downloads/
    echo    IMPORTANTE: marque "Add Python to PATH"
    pause
    exit /b 1
)
echo    ✅ Python OK.

REM --- Cria venv ---
echo.
echo [2/4] Criando ambiente virtual...
if not exist "%PYTHON_EXE%" (
    python -m venv "%VENV_DIR%"
    echo    ✅ venv criado.
) else (
    echo    ✅ venv ja existe.
)

REM --- Atualiza pip ---
echo.
echo [3/4] Atualizando pip...
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet
echo    ✅ pip atualizado.

REM --- Instala dependencias ---
echo.
echo [4/4] Instalando dependencias...
if exist "%REQUIREMENTS%" (
    "%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS%"
) else (
    "%PYTHON_EXE%" -m pip install flask flask-cors pandas numpy openpyxl bcrypt requests python-dotenv
)
echo    ✅ Dependencias instaladas.

echo.
echo ============================================================
echo   ✅ INSTALACAO CONCLUIDA
echo ============================================================
echo.
echo   📡 IP detectado: !HOST!
echo   ▶  Agora rode "iniciar_servidores.bat" para subir o servidor
echo.
pause
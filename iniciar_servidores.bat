@echo off
title Vilavelhense FC - Servidores (IP Automatico)
setlocal enabledelayedexpansion

REM ============================================================
REM CONFIGURACOES
REM ============================================================
set "BACKEND_DIR=%~dp0"
set "BACKEND_DIR=%BACKEND_DIR:~0,-1%"
set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"
set "PORT=5000"

echo ============================================================
echo   VILAVELHENSE FC - INICIANDO SERVIDORES
echo ============================================================
echo.

REM ============================================================
REM 1. DETECTA O IP DO PC AUTOMATICAMENTE
REM ============================================================
echo [1/4] Detectando IP do computador...
set "HOST="

REM --- Tentativa 1: PowerShell (mais confiavel) ---
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '169.*' -and $_.IPAddress -notlike '127.*' -and $_.InterfaceAlias -notlike '*Loopback*' -and $_.InterfaceAlias -notlike '*Virtual*' -and $_.InterfaceAlias -notlike '*VMware*' -and $_.InterfaceAlias -notlike '*Hyper-V*' } | Sort-Object InterfaceMetric | Select-Object -First 1 -ExpandProperty IPAddress"`) do (
    set "HOST=%%a"
)

REM --- Tentativa 2: ipconfig (fallback) ---
if "!HOST!"=="" (
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
        if "!HOST!"=="" (
            set "IP_TEMP=%%a"
            set "IP_TEMP=!IP_TEMP: =!"
            set "HOST=!IP_TEMP!"
        )
    )
)

if "!HOST!"=="" (
    echo.
    echo ❌ ERRO: Nao foi possivel detectar o IP automaticamente.
    echo    Verifique se voce esta conectado a uma rede.
    echo.
    pause
    exit /b 1
)

echo     ✅ IP detectado: !HOST!
echo.

REM ============================================================
REM 2. VERIFICA O VENV
REM ============================================================
echo [2/4] Verificando ambiente virtual...
if not exist "%PYTHON_EXE%" (
    echo.
    echo ❌ ERRO: Ambiente virtual nao encontrado!
    echo    Execute primeiro "instalar_backend.bat"
    echo.
    pause
    exit /b 1
)
echo     ✅ Ambiente virtual OK.

REM ============================================================
REM 3. VERIFICA O NGROK
REM ============================================================
echo.
echo [3/4] Verificando ngrok...
ngrok --version >nul 2>&1
if errorlevel 1 (
    echo     ⚠️  ngrok nao encontrado. O app so funcionara na rede local.
    set "HAS_NGROK=0"
) else (
    echo     ✅ ngrok encontrado.
    set "HAS_NGROK=1"
)

REM ============================================================
REM 4. INICIA OS SERVIDORES
REM ============================================================
echo.
echo [4/4] Iniciando servidores...
echo.

cd /d "%BACKEND_DIR%"

REM Inicia o Flask
start "Flask - Vilavelhense" "%PYTHON_EXE%" app.py
echo     ✅ Flask iniciado
echo        📡 http://!HOST!:%PORT%

timeout /t 3 /nobreak >nul

REM Inicia o ngrok (se existir)
if "!HAS_NGROK!"=="1" (
    start "ngrok - Vilavelhense" ngrok http %PORT%
    echo     ✅ ngrok iniciado (veja a URL na janela do ngrok)
    echo.
    echo     ⚠️  IMPORTANTE: copie a URL do ngrok e envie para o testador
    echo        Exemplo: https://abc123.ngrok-free.dev
) else (
    echo     ⚠️  ngrok nao iniciado
)

REM ============================================================
REM 5. EXIBE UM ARQUIVO TXT COM O IP (para o app)
REM ============================================================
echo !HOST! > "%BACKEND_DIR%\ip_atual.txt"
echo.
echo     📝 IP salvo em: ip_atual.txt

REM ============================================================
REM RESUMO FINAL
REM ============================================================
echo.
echo ============================================================
echo   ✅ SERVIDORES RODANDO
echo ============================================================
echo.
echo   📡 IP do PC:  !HOST!
echo   🔌 Flask:     http://!HOST!:%PORT%
echo   🩺 Health:    http://!HOST!:%PORT%/api/health
if "!HAS_NGROK!"=="1" (
    echo   🌐 ngrok:     veja a URL na janela do ngrok
)
echo.
echo   ⚠️  NAO FECHE ESTA JANELA NEM A DO FLASK/NGROK
echo   ⚠️  O celular deve estar na MESMA rede Wi-Fi
echo.
pause >nul
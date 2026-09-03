@echo off
title Vilavelhense FC - Servidores com Fallback e ngrok

REM ============================================================
REM CONFIGURE AQUI OS IPs (casa e faculdade)
REM ============================================================
set "IP_CASA=192.168.1.107"
set "IP_FACULDADE=172.27.60.223"

REM ============================================================
REM TESTA CONECTIVIDADE COM O IP DE CASA
REM ============================================================
ping -n 1 %IP_CASA% > nul
if %errorlevel% equ 0 (
    set "HOST=%IP_CASA%"
    echo ✅ Conectado em casa - usando IP: %HOST%
) else (
    set "HOST=%IP_FACULDADE%"
    echo 🌐 Conectado na faculdade - usando IP: %HOST%
)

REM ============================================================
REM DIRETÓRIO DO BACKEND
REM ============================================================
set "BACKEND_DIR=D:\VilavelhenseBackend"
cd /d "%BACKEND_DIR%" || (
    echo ❌ Diretório não encontrado!
    pause
    exit /b
)

echo ========================================
echo  🚀 Iniciando Servidores em %HOST%
echo ========================================
echo.

REM ============================================================
REM 1. FASTAPI (porta 8000)
REM ============================================================
echo 📡 Iniciando FastAPI...
start "FastAPI" .\venv\Scripts\python.exe -m uvicorn api:app --host %HOST% --port 8000 --reload
timeout /t 3 /nobreak > nul

REM ============================================================
REM 2. FLASK (porta 5000)
REM ============================================================
echo 🐍 Iniciando Flask...
start "Flask" .\venv\Scripts\python.exe app.py
timeout /t 3 /nobreak > nul

REM ============================================================
REM 3. NGROK (túnel público para 4G)
REM ============================================================
echo 🌐 Iniciando ngrok (túnel público para 4G)...
start "ngrok" ngrok http 5000

echo.
echo ========================================
echo  ✅ TODOS OS SERVIÇOS INICIADOS!
echo ========================================
echo.
echo    📡 FastAPI: http://%HOST%:8000
echo    🐍 Flask:   http://%HOST%:5000
echo    🌐 ngrok:   https://spew-custodian-serve.ngrok-free.dev
echo.
echo    📌 Para usar no 4G, atualize o URL no arquivo:
echo       src/api/index.js
echo       com a URL do ngrok (que pode mudar a cada sessão)
echo.
echo    🔗 Interface do ngrok: http://127.0.0.1:4040
echo.
pause
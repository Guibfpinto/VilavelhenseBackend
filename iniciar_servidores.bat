@echo off
title Vilavelhense FC - Servidores com Fallback

REM ===== CONFIGURE AQUI OS IPs =====
set "IP_CASA=192.168.1.107"
set "IP_FACULDADE=172.27.60.223"

REM ===== Testa conectividade com o IP de casa =====
ping -n 1 %IP_CASA% > nul
if %errorlevel% equ 0 (
    set "HOST=%IP_CASA%"
    echo ✅ Conectado em casa - usando IP: %HOST%
) else (
    set "HOST=%IP_FACULDADE%"
    echo 🌐 Conectado na faculdade - usando IP: %HOST%
)

REM ===== Diretório do backend (ajuste se necessário) =====
set "BACKEND_DIR=D:\VilavelhenseBackend"
cd /d "%BACKEND_DIR%" || (
    echo ❌ Diretório não encontrado!
    pause
    exit /b
)

echo ========================================
echo  🚀 Iniciando Servidores em %HOST%
echo ========================================

start "FastAPI" .\venv\Scripts\python.exe -m uvicorn api:app --host %HOST% --port 8000 --reload
timeout /t 3 /nobreak > nul
start "Flask" .\venv\Scripts\python.exe app.py

echo.
echo ✅ Servidores rodando em %HOST%
echo    FastAPI: http://%HOST%:8000
echo    Flask:   http://%HOST%:5000
echo.
pause
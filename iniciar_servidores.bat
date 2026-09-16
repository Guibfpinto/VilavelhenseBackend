@echo off
title Vilavelhense FC - Servidores (Funnel + Backend)
setlocal enabledelayedexpansion

REM ============================================================
REM CONFIGURACOES
REM ============================================================
set "BACKEND_DIR=%~dp0"
set "BACKEND_DIR=%BACKEND_DIR:~0,-1%"
set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"
set "FLASK_PORT=5000"
set "FASTAPI_PORT=8000"
set "FUNNEL_URL=https://notebook-gbfp.tailc517f2.ts.net"

echo ============================================================
echo   VILAVELHENSE FC - INICIANDO SERVIDORES
echo ============================================================
echo.

REM ============================================================
REM 1. VERIFICA O VENV
REM ============================================================
echo [1/5] Verificando ambiente virtual...
if not exist "%PYTHON_EXE%" (
    echo.
    echo ❌ ERRO: venv nao encontrado em:
    echo    %PYTHON_EXE%
    echo.
    echo    Execute primeiro "instalar_backend.bat"
    echo.
    pause
    exit /b 1
)
echo     ✅ venv OK

REM ============================================================
REM 2. VERIFICA O TAILSCALE
REM ============================================================
echo.
echo [2/5] Verificando Tailscale...
tailscale status >nul 2>&1
if errorlevel 1 (
    echo     ❌ ERRO: Tailscale nao encontrado ou nao logado!
    echo        Instale em https://tailscale.com/download
    echo        E faca login com sua conta.
    pause
    exit /b 1
)
echo     ✅ Tailscale ativo

REM ============================================================
REM 3. CONFIGURA O TAILSCALE FUNNEL (PRIMEIRO)
REM ============================================================
echo.
echo [3/5] Configurando Tailscale Funnel para a porta %FLASK_PORT%...

REM Limpa qualquer configuracao anterior
echo     🔄 Resetando configuracao anterior...
tailscale serve reset >nul 2>&1

REM Ativa o Funnel na porta 5000
echo     🔄 Ativando Funnel na porta %FLASK_PORT%...
tailscale funnel %FLASK_PORT% >nul 2>&1

if errorlevel 1 (
    echo     ⚠️  Falha ao ativar Funnel automaticamente
    echo        Execute manualmente: tailscale funnel %FLASK_PORT%
) else (
    echo     ✅ Funnel ativo em %FUNNEL_URL%
)

REM Aguarda o Funnel estar pronto
timeout /t 2 /nobreak >nul

REM ============================================================
REM 4. INICIA A FASTAPI (porta 8000)
REM ============================================================
echo.
echo [4/5] Iniciando FastAPI (porta %FASTAPI_PORT%)...
cd /d "%BACKEND_DIR%"

if not exist "%BACKEND_DIR%\api.py" (
    echo     ⚠️  api.py nao encontrado. Pulando FastAPI.
) else (
    start "FastAPI - Vilavelhense" cmd /k ""%PYTHON_EXE%" -m uvicorn api:app --host 127.0.0.1 --port %FASTAPI_PORT%"
    echo     ✅ FastAPI iniciado
)

timeout /t 3 /nobreak >nul

REM ============================================================
REM 5. INICIA O FLASK / APP.PY (porta 5000)
REM ============================================================
echo.
echo [5/5] Iniciando Flask (app.py - porta %FLASK_PORT%)...

if not exist "%BACKEND_DIR%\app.py" (
    echo.
    echo ❌ ERRO: app.py nao encontrado em:
    echo    %BACKEND_DIR%\app.py
    pause
    exit /b 1
)

start "Flask - Vilavelhense" cmd /k ""%PYTHON_EXE%" app.py"
echo     ✅ Flask iniciado

REM Aguarda o Flask subir
timeout /t 4 /nobreak >nul

REM ============================================================
REM TESTE AUTOMATICO DO HEALTH
REM ============================================================
echo.
echo [BONUS] Testando conexao...
timeout /t 2 /nobreak >nul

curl.exe -s http://localhost:%FLASK_PORT%/api/health >nul 2>&1
if errorlevel 1 (
    echo     ⚠️  Flask ainda nao respondeu. Verifique a janela do Flask.
) else (
    echo     ✅ Flask respondendo em http://localhost:%FLASK_PORT%
)

curl.exe -s %FUNNEL_URL%/api/health >nul 2>&1
if errorlevel 1 (
    echo     ⚠️  Funnel ainda nao respondeu. Aguarde alguns segundos.
) else (
    echo     ✅ Funnel respondendo em %FUNNEL_URL%
)

REM ============================================================
REM RESUMO FINAL
REM ============================================================
echo.
echo ============================================================
echo   ✅ SERVIDORES RODANDO
echo ============================================================
echo.
echo   🌐 Funnel:     %FUNNEL_URL%
echo   🐍 Flask:      http://localhost:%FLASK_PORT%
echo   ⚡ FastAPI:    http://localhost:%FASTAPI_PORT%
echo.
echo   🩺 Health:     %FUNNEL_URL%/api/health
echo   📚 FastAPI:    %FUNNEL_URL%/fastapi/docs
echo.
echo   ⚠️  NAO FECHE AS JANELAS DO FLASK E FASTAPI
echo   ⚠️  Mantenha o Tailscale ativo
echo.
echo   Pressione qualquer tecla para sair desta janela...
pause >nul
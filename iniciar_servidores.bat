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
    echo ❌ ERRO: venv nao encontrado!
    echo    Execute primeiro "instalar_backend.bat"
    pause
    exit /b 1
)
echo     [OK] venv

REM ============================================================
REM 2. VERIFICA O TAILSCALE
REM ============================================================
echo.
echo [2/5] Verificando Tailscale...
tailscale status >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Tailscale nao encontrado ou nao logado!
    pause
    exit /b 1
)
echo     [OK] Tailscale ativo

REM ============================================================
REM 3. RESETA O FUNNEL ANTERIOR
REM ============================================================
echo.
echo [3/5] Resetando Funnel anterior...

REM Reseta em background (nao trava)
start /B /WAIT cmd /c "tailscale serve reset >nul 2>&1"

echo     [OK] Reset concluido

REM ============================================================
REM 4. ATIVA O FUNNEL EM BACKGROUND
REM ============================================================
echo.
echo [4/5] Ativando Funnel na porta %FLASK_PORT%...

REM --bg roda em background (nao trava o terminal)
REM --yes aceita qualquer confirmacao automaticamente
start /B /WAIT cmd /c "tailscale funnel --bg --yes %FLASK_PORT% >nul 2>&1"

echo     [OK] Funnel configurado
echo     URL: %FUNNEL_URL%

REM Aguarda o Funnel ficar pronto
timeout /t 3 /nobreak >nul

REM ============================================================
REM 5. INICIA O FLASK
REM ============================================================
echo.
echo [5/5] Iniciando Flask (app.py - porta %FLASK_PORT%)...

if not exist "%BACKEND_DIR%\app.py" (
    echo ❌ ERRO: app.py nao encontrado!
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"
start "Flask - Vilavelhense" cmd /k ""%PYTHON_EXE%" app.py"
echo     [OK] Flask iniciado

REM Aguarda o Flask subir
timeout /t 5 /nobreak >nul

REM ============================================================
REM TESTE AUTOMATICO
REM ============================================================
echo.
echo [BONUS] Testando conexoes...

REM Testa Flask local
curl.exe -s --max-time 5 http://localhost:%FLASK_PORT%/api/health | findstr "ok" >nul 2>&1
if errorlevel 1 (
    echo     [!] Flask ainda nao respondeu
) else (
    echo     [OK] Flask respondendo em http://localhost:%FLASK_PORT%
)

REM Testa Funnel externo
curl.exe -s --max-time 10 %FUNNEL_URL%/api/health | findstr "ok" >nul 2>&1
if errorlevel 1 (
    echo     [!] Funnel ainda nao respondeu (aguarde alguns segundos)
) else (
    echo     [OK] Funnel respondendo em %FUNNEL_URL%
)

REM ============================================================
REM RESUMO
REM ============================================================
echo.
echo ============================================================
echo   SERVIDORES RODANDO
echo ============================================================
echo.
echo   Funnel:    %FUNNEL_URL%
echo   Flask:     http://localhost:%FLASK_PORT%
echo.
echo   Health:    %FUNNEL_URL%/api/health
echo.
echo   NAO FECHE AS JANELAS DO FLASK
echo   Mantenha o Tailscale ativo
echo.
pause >nul
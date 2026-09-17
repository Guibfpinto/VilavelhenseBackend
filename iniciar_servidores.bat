@echo off

REM 🔥 Se não foi chamado com "minimized", reinicia minimizado
if not "%1"=="minimized" (
    start /min cmd /c "%~f0" minimized
    exit /b
)

title Vilavelhense FC - Servidores (Funnel + Backend)
setlocal enabledelayedexpansion

REM 🔥 Aguarda 60s para o Windows/Tailscale/rede iniciarem
echo Aguardando inicializacao do Windows (60s)...
timeout /t 60 /nobreak >nul
echo [OK] Iniciando servidores...

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
    echo ERRO: venv nao encontrado!
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
    echo ERRO: Tailscale nao encontrado ou nao logado!
    pause
    exit /b 1
)
echo     [OK] Tailscale ativo

REM ============================================================
REM 3. RESETA O FUNNEL ANTERIOR
REM ============================================================
echo.
echo [3/5] Resetando Funnel anterior...
start /B /WAIT cmd /c "tailscale serve reset >nul 2>&1"
echo     [OK] Reset concluido

REM ============================================================
REM 4. ATIVA O FUNNEL EM BACKGROUND
REM ============================================================
echo.
echo [4/5] Ativando Funnel na porta %FLASK_PORT%...
start /B /WAIT cmd /c "tailscale funnel --bg --yes %FLASK_PORT% >nul 2>&1"
echo     [OK] Funnel configurado
echo     URL: %FUNNEL_URL%
timeout /t 3 /nobreak >nul

REM ============================================================
REM 5. INICIA O FLASK (MINIMIZADO)
REM ============================================================
echo.
echo [5/5] Iniciando Flask (app.py - porta %FLASK_PORT%)...

if not exist "%BACKEND_DIR%\app.py" (
    echo ERRO: app.py nao encontrado!
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"

REM 🔥 Flask minimizado
start /min "Flask - Vilavelhense" cmd /k ""%PYTHON_EXE%" app.py"
echo     [OK] Flask iniciado (minimizado)

REM Aguarda o Flask subir
timeout /t 5 /nobreak >nul

REM ============================================================
REM 5.1. INICIA A FASTAPI (MINIMIZADO) - SE EXISTIR
REM ============================================================
if exist "%BACKEND_DIR%\api.py" (
    echo.
    echo [5.1] Iniciando FastAPI (porta %FASTAPI_PORT%)...
    REM 🔥 FastAPI minimizada
    start /min "FastAPI - Vilavelhense" cmd /k ""%PYTHON_EXE%" -m uvicorn api:app --host 127.0.0.1 --port %FASTAPI_PORT%"
    echo     [OK] FastAPI iniciado (minimizado)
    timeout /t 3 /nobreak >nul
) else (
    echo.
    echo [!] api.py nao encontrado. FastAPI nao iniciada.
)

REM ============================================================
REM TESTE AUTOMATICO
REM ============================================================
echo.
echo [BONUS] Testando conexoes...

curl.exe -s --max-time 5 http://localhost:%FLASK_PORT%/api/health | findstr "ok" >nul 2>&1
if errorlevel 1 (
    echo     [!] Flask ainda nao respondeu
) else (
    echo     [OK] Flask respondendo em http://localhost:%FLASK_PORT%
)

curl.exe -s --max-time 10 %FUNNEL_URL%/api/health | findstr "ok" >nul 2>&1
if errorlevel 1 (
    echo     [!] Funnel ainda nao respondeu
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
echo   FastAPI:   http://localhost:%FASTAPI_PORT%
echo.
echo   Health:    %FUNNEL_URL%/api/health
echo.
echo   Todas as janelas estao MINIMIZADAS
echo   Verifique a barra de tarefas para acessa-las
echo.
echo   Esta janela fecha em 15 segundos...

timeout /t 15 /nobreak >nul
exit /b 0
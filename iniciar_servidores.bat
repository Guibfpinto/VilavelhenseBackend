@echo off

REM Se nao foi chamado com "minimized", reinicia minimizado
if not "%1"=="minimized" (
    start /min cmd /c "%~f0" minimized
    exit /b
)

title Vilavelhense FC - Servidores (Funnel + Backend + IA)
setlocal enabledelayedexpansion

REM Aguarda 60s para o Windows/Tailscale/Docker/rede iniciarem
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

REM --- PitchMind (IA) ---
REM Se o PitchMind estiver em OUTRA maquina, coloque PITCHMIND_LOCAL=0 e ajuste PITCHMIND_URL
set "PITCHMIND_LOCAL=0"
set "PITCHMIND_DIR=D:\pitchmind"
set "PITCHMIND_PY=%PITCHMIND_DIR%\.venv\Scripts\python.exe"
set "PITCHMIND_PORT=5001"
set "PITCHMIND_URL=http://100.118.148.32:%PITCHMIND_PORT%"
REM Estas variaveis sao herdadas pelo Flask e pelo PitchMind
set "PITCHMIND_HOST=100.118.148.32"

echo ============================================================
echo   VILAVELHENSE FC - INICIANDO SERVIDORES + IA
echo ============================================================
echo.

REM ============================================================
REM 1. VERIFICA O VENV
REM ============================================================
echo [1/7] Verificando ambiente virtual...
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
echo [2/7] Verificando Tailscale...
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
echo [3/7] Resetando Funnel anterior...
start /B /WAIT cmd /c "tailscale serve reset >nul 2>&1"
echo     [OK] Reset concluido

REM ============================================================
REM 4. ATIVA O FUNNEL EM BACKGROUND (aponta para o Flask)
REM ============================================================
echo.
echo [4/7] Ativando Funnel na porta %FLASK_PORT%...
start /B /WAIT cmd /c "tailscale funnel --bg --yes %FLASK_PORT% >nul 2>&1"
echo     [OK] Funnel configurado
echo     URL: %FUNNEL_URL%
timeout /t 3 /nobreak >nul

REM ============================================================
REM 5. IA - BANCO (DOCKER) + PITCHMIND
REM ============================================================
echo.
echo [5/7] Iniciando IA (PitchMind)...

if not "%PITCHMIND_LOCAL%"=="1" (
    echo     [i] PitchMind remoto: %PITCHMIND_URL% - nada a iniciar aqui
    goto :pitchmind_fim
)

if not exist "%PITCHMIND_PY%" (
    echo     [!] Python do PitchMind nao encontrado: %PITCHMIND_PY%
    echo     [!] A IA nao sera iniciada. Corrija PITCHMIND_DIR neste arquivo.
    goto :pitchmind_fim
)

REM 5.1 Banco Postgres do PitchMind (Docker Desktop precisa estar ativo)
set "TENTATIVAS=0"
:esperar_docker
docker info >nul 2>&1
if not errorlevel 1 goto :docker_ok
set /a TENTATIVAS+=1
if %TENTATIVAS% GEQ 12 goto :docker_falhou
echo     Aguardando Docker Desktop... (%TENTATIVAS%/12)
timeout /t 5 /nobreak >nul
goto :esperar_docker

:docker_falhou
echo     [!] Docker nao respondeu. O PitchMind sobe, mas sem banco de dados.
goto :iniciar_pitchmind

:docker_ok
echo     [OK] Docker ativo
pushd "%PITCHMIND_DIR%"
docker compose up -d db >nul 2>&1
popd
echo     [OK] Banco do PitchMind iniciado
timeout /t 5 /nobreak >nul

REM 5.2 API do PitchMind (minimizada)
:iniciar_pitchmind
start /min "PitchMind - IA" /d "%PITCHMIND_DIR%" cmd /k ""%PITCHMIND_PY%" api_http.py"
echo     [OK] PitchMind iniciado (minimizado) - porta %PITCHMIND_PORT%
timeout /t 5 /nobreak >nul

:pitchmind_fim

REM ============================================================
REM 6. INICIA O FLASK (MINIMIZADO)
REM ============================================================
echo.
echo [6/7] Iniciando Flask (app.py - porta %FLASK_PORT%)...

if not exist "%BACKEND_DIR%\app.py" (
    echo ERRO: app.py nao encontrado!
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"

REM Flask minimizado (herda PITCHMIND_URL)
start /min "Flask - Vilavelhense" cmd /k ""%PYTHON_EXE%" app.py"
echo     [OK] Flask iniciado (minimizado)

REM Aguarda o Flask subir
timeout /t 5 /nobreak >nul

REM ============================================================
REM 7. INICIA A FASTAPI (MINIMIZADO) - SE EXISTIR
REM ============================================================
echo.
echo [7/7] FastAPI...
if exist "%BACKEND_DIR%\api.py" (
    echo     Iniciando FastAPI (porta %FASTAPI_PORT%)...
    start /min "FastAPI - Vilavelhense" cmd /k ""%PYTHON_EXE%" -m uvicorn api:app --host 127.0.0.1 --port %FASTAPI_PORT%"
    echo     [OK] FastAPI iniciado (minimizado)
    timeout /t 3 /nobreak >nul
) else (
    echo     [!] api.py nao encontrado. FastAPI nao iniciada.
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

REM Confirma a cadeia completa: Flask -> PitchMind
curl.exe -s --max-time 10 http://localhost:%FLASK_PORT%/api/ecossistema/ia/status | findstr "true" >nul 2>&1
if errorlevel 1 (
    echo     [!] IA: Flask nao alcanca o PitchMind ainda ^(pode estar a carregar^)
) else (
    echo     [OK] IA respondendo ^(Flask -^> PitchMind^)
)

REM ============================================================
REM RESUMO
REM ============================================================
echo.
echo ============================================================
echo   SERVIDORES RODANDO
echo ============================================================
echo.
echo   Funnel:     %FUNNEL_URL%
echo   Flask:      http://localhost:%FLASK_PORT%
echo   FastAPI:    http://localhost:%FASTAPI_PORT%
echo   PitchMind:  %PITCHMIND_URL%
echo.
echo   Health:     %FUNNEL_URL%/api/health
echo   Status IA:  %FUNNEL_URL%/api/ecossistema/ia/status
echo.
echo   Todas as janelas estao MINIMIZADAS
echo   Verifique a barra de tarefas para acessa-las
echo.
echo   Esta janela fecha em 15 segundos...

timeout /t 15 /nobreak >nul
exit /b 0

@echo off
chcp 65001 > nul
title Vilavelhense FC - Servidores

echo ========================================
echo  🚀 Iniciando Servidores do Vilavelhense
echo ========================================
echo.

REM Ativa o ambiente virtual
call .\venv\Scripts\Activate

REM Inicia a FastAPI (porta 8000)
start "FastAPI" .\venv\Scripts\python.exe -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

REM Aguarda 3 segundos
timeout /t 3 /nobreak > nul

REM Inicia o Flask (porta 5000)
start "Flask" .\venv\Scripts\python.exe app.py

echo.
echo ✅ Servidores iniciados!
echo    FastAPI: http://localhost:8000
echo    Flask:   http://localhost:5000
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause > nul
@echo off
chcp 65001 > nul
echo ==============================================
echo Iniciando CineAI - Sistema de Recomendacao
echo ==============================================

echo [1/3] Verificando e instalando dependencias...
pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Iniciando backend (FastAPI) em uma nova janela...
start cmd /k "cd backend && uvicorn api:app --host 0.0.0.0 --port 8000"

echo.
echo [3/3] Abrindo frontend no navegador...
:: Aguarda alguns segundos para a API subir
timeout /t 3 /nobreak >nul
start frontend\index.html

echo.
echo ==============================================
echo Servidor iniciado com sucesso!
echo Feche esta janela se desejar.
echo ==============================================
pause

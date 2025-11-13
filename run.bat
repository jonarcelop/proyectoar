@echo off
REM Script para ejecutar el proyecto en Windows

echo === Triqui Online - Setup Script ===
echo.

REM 1. Backend
echo 1. Instalando dependencias del servidor...
cd server
pip install -r requirements.txt
echo [OK] Dependencias instaladas
echo.

REM 2. Tests (opcional)
set /p run_tests="Ejecutar tests? (s/n): "
if /i "%run_tests%"=="s" (
    echo 2. Ejecutando tests...
    pytest tests/ -v --cov=models --cov=utils --cov=ai --cov-report=html
    echo [OK] Tests completados. Reporte en htmlcov/index.html
    echo.
)

REM 3. Servidor
cd ..
echo 3. Iniciando servidor FastAPI...
echo    URL: http://localhost:8000
echo    WebSocket: ws://localhost:8000/ws
echo.
echo Presiona Ctrl+C para detener
echo.
cd server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

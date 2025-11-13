#!/bin/bash
# Script para ejecutar el proyecto completo

echo "=== Triqui Online - Setup Script ==="

# 1. Backend
echo "1. Instalando dependencias del servidor..."
cd server
pip install -r requirements.txt
echo "✓ Dependencias instaladas"

# 2. Tests (opcional)
read -p "¿Ejecutar tests? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "2. Ejecutando tests..."
    pytest tests/ -v --cov=models --cov=utils --cov=ai --cov-report=html
    echo "✓ Tests completados. Reporte en htmlcov/index.html"
fi

# 3. Servidor
cd ..
echo "3. Iniciando servidor FastAPI..."
echo "   URL: http://localhost:8000"
echo "   WebSocket: ws://localhost:8000/ws"
echo ""
echo "Press Ctrl+C to stop"
cd server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

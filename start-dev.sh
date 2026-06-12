#!/bin/bash

# UniGrade Development Environment Startup Script
# Inicia backend FastAPI + frontend Vite em paralelo

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/.venv"

echo "🚀 UniGrade Development Environment"
echo "====================================="
echo ""

# Verificar virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment não encontrado em $VENV_PATH"
    echo "📝 Crie com: python -m venv .venv && pip install -e '.[dev]'"
    exit 1
fi

# Ativar virtual environment
echo "✓ Ativando Python virtual environment..."
source "$VENV_PATH/bin/activate"

# Verificar que uvicorn está instalado
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn não encontrado. Execute: pip install -e '.[dev]'"
    exit 1
fi

# Verificar que npm está instalado
if ! command -v npm &> /dev/null; then
    echo "❌ npm não encontrado. Instale Node.js."
    exit 1
fi

echo ""
echo "📋 Iniciando serviços..."
echo ""
echo "  Terminal 1 (Backend):  http://localhost:8000"
echo "  Terminal 2 (Frontend): http://localhost:5173"
echo ""
echo "⏸️  Pressione Ctrl+C em AMBOS os terminais para parar."
echo ""

# Função para limpar processes ao sair
cleanup() {
    echo ""
    echo "🛑 Parando serviços..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "✓ Serviços parados."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Terminal 1: Backend FastAPI
echo "🔧 Backend FastAPI iniciando..."
(
    cd "$PROJECT_ROOT"
    uvicorn backend.app.main:app --reload --port 8000
) &
BACKEND_PID=$!

# Aguardar inicialização do backend
sleep 3

# Terminal 2: Frontend Vite
echo "🎨 Frontend Vite iniciando..."
(
    cd "$PROJECT_ROOT/client"
    npm run dev
) &
FRONTEND_PID=$!

echo ""
echo "✅ Ambos os serviços iniciados!"
echo ""

# Aguardar indefinidamente
wait

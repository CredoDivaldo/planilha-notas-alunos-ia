#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
echo "🗄️  A aplicar migrações da base de dados (schema normalizado)..."
python -m backend.app.cli bootstrap-db || echo "⚠️  Para uma base de dados limpa: python -m backend.app.cli bootstrap-db --force"
echo "🚀 Backend FastAPI iniciando..."
echo "📍 API em: http://localhost:8000"
echo "📊 Health: http://localhost:8000/api/v1/health"
echo "🔐 Login: POST http://localhost:8000/auth/login"
echo ""
python -m uvicorn backend.app.main:app --reload --port 8000

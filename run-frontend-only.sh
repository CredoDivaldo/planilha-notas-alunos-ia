#!/bin/bash
cd "$(dirname "$0")/client"
echo "🎨 Frontend Vite iniciando..."
echo "📍 App em: http://localhost:5173"
echo "⚠️  Certifique-se que backend está a correr em outro terminal:"
echo "   ./run-backend-only.sh"
echo ""
npm run dev

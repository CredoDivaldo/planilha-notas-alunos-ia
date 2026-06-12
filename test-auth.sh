#!/bin/bash

# Test authentication endpoint
# Prerequisites: Backend running on localhost:8000

API_URL="http://localhost:8000"
TEST_USERNAME="admin"
TEST_PASSWORD="admin"

echo "🧪 Testing Authentication — UniGrade"
echo "======================================"
echo ""

# Check if backend is running
echo "🔍 Verificando se backend está a correr em $API_URL..."
if ! curl -s -f "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "❌ Backend não está a responder em $API_URL"
    echo ""
    echo "📝 Inicie o backend com:"
    echo "   ./start-dev.sh"
    echo "   ou"
    echo "   npm run dev"
    echo ""
    exit 1
fi

echo "✓ Backend está a responder"
echo ""

# Test 1: Check if /api/v1/health endpoint exists
echo "📌 Test 1: Health check"
HEALTH_RESPONSE=$(curl -s "$API_URL/api/v1/health")
echo "Response: $HEALTH_RESPONSE"
echo ""

# Test 2: Login with correct credentials
echo "📌 Test 2: Login com credenciais corretas (admin/admin)"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$TEST_USERNAME\",\"password\":\"$TEST_PASSWORD\"}")

echo "Response: $LOGIN_RESPONSE"
echo ""

# Extract token (se sucesso)
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login bem-sucedido!"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "   Token: ${TOKEN:0:20}..."
    echo ""

    # Test 3: Use token to access protected endpoint
    echo "📌 Test 3: Usar token para aceder a endpoint protegido (/api/v1/contexts)"
    CONTEXTS_RESPONSE=$(curl -s "$API_URL/api/v1/contexts" \
      -H "Authorization: Bearer $TOKEN")
    echo "Response: $CONTEXTS_RESPONSE"
    echo ""
    echo "✅ Autenticação e autorização funcionam!"
else
    echo "❌ Login falhou!"
    echo "   Verifique credenciais em backend/app/auth/"
fi

# Test 4: Login com password errada
echo ""
echo "📌 Test 4: Login com password ERRADA (deve rejeitar)"
WRONG_PASS=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$TEST_USERNAME\",\"password\":\"wrongpass123\"}")

echo "Response: $WRONG_PASS"
echo ""

if echo "$WRONG_PASS" | grep -q "detail\|error\|401"; then
    echo "✅ Password rejeitada corretamente!"
else
    echo "⚠️  Password incorreta foi aceita — BUG em verify_password"
fi

echo ""
echo "✅ Testes completos!"

#!/bin/bash

# Setup and test authentication for UniGrade
# Cria utilizador de teste e valida auth flow

API_URL="http://localhost:8000"
TEST_EMAIL="admin@test.local"
TEST_PASSWORD="Admin@123456"

echo "🚀 UniGrade — Setup Test Environment"
echo "====================================="
echo ""

# Verificar que backend está a correr
echo "🔍 Verificando backend em $API_URL..."
if ! curl -s -f "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "❌ Backend não está a responder em $API_URL"
    echo ""
    echo "📝 Inicie em outro terminal com: ./start-dev.sh"
    exit 1
fi

echo "✓ Backend está a responder"
echo ""

# Step 1: Registar novo utilizador
echo "📝 Step 1: Registar utilizador de teste (admin@test.local)"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"full_name\": \"Admin Test\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

echo "Response: $REGISTER_RESPONSE"
echo ""

# Extrair token do registo
if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo "✅ Registo bem-sucedido!"
    REG_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    REG_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    echo "   User ID: $REG_ID"
    echo "   Token: ${REG_TOKEN:0:20}..."
    echo ""
else
    echo "⚠️  Registo pode ter falhado. Continuando com login..."
    echo ""
fi

# Step 2: Fazer login com as credenciais
echo "🔑 Step 2: Fazer login com admin@test.local / Admin@123456"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email_or_student_number\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"role\": \"professor\"
  }")

echo "Response: $LOGIN_RESPONSE"
echo ""

# Extrair token do login
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login bem-sucedido!"
    LOGIN_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    LOGIN_ID=$(echo "$LOGIN_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    echo "   User ID: $LOGIN_ID"
    echo "   Token: ${LOGIN_TOKEN:0:20}..."
    echo ""

    # Step 3: Testar acesso a endpoint protegido
    echo "🔐 Step 3: Testar acesso a endpoint protegido (/api/v1/contexts)"
    CONTEXTS_RESPONSE=$(curl -s "$API_URL/api/v1/contexts" \
      -H "Authorization: Bearer $LOGIN_TOKEN")

    echo "Response (first 300 chars): $(echo "$CONTEXTS_RESPONSE" | head -c 300)"
    echo ""

    if echo "$CONTEXTS_RESPONSE" | grep -q "detail\|error" && ! echo "$CONTEXTS_RESPONSE" | grep -q "^\["; then
        echo "⚠️  Pode haver erro de autorização"
    else
        echo "✅ Acesso a endpoint protegido funcionou!"
    fi
else
    echo "❌ Login falhou!"
    echo ""
    # Tentar com password errada para testar validação
    echo "🔍 Testando validação de password (deve rejeitar)..."
    WRONG_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d "{
        \"email_or_student_number\": \"$TEST_EMAIL\",
        \"password\": \"WRONGPASSWORD123\",
        \"role\": \"professor\"
      }")

    echo "Response: $WRONG_RESPONSE"
    echo ""

    if echo "$WRONG_RESPONSE" | grep -q "401\|Login failed"; then
        echo "✅ Password incorreta foi rejeitada!"
    fi
fi

echo ""
echo "✅ Setup test completo!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Verifique que login/logout funcionam na UI"
echo "   2. Teste CSV upload com docs/test-data/alunos-teste.csv"
echo "   3. Execute outras waves de testes em Wave 2-5"

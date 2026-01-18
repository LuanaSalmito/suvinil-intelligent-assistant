#!/bin/bash

# Script de teste da API
# Uso: ./test_api.sh

API_URL="http://localhost:8000"

echo "🧪 Testando API Suvinil AI"
echo "=========================="
echo ""

# 1. Health Check
echo "1️⃣ Testando Health Check..."
curl -s "$API_URL/health" | jq '.' || echo "❌ API não está respondendo"
echo ""

# 2. Login como Admin
echo "2️⃣ Fazendo login como admin..."
ADMIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

ADMIN_TOKEN=$(echo $ADMIN_RESPONSE | jq -r '.access_token')

if [ "$ADMIN_TOKEN" != "null" ] && [ -n "$ADMIN_TOKEN" ]; then
  echo "✅ Login admin bem-sucedido"
  echo "Token: ${ADMIN_TOKEN:0:50}..."
else
  echo "❌ Falha no login admin"
  echo "Resposta: $ADMIN_RESPONSE"
  exit 1
fi
echo ""

# 3. Login como User
echo "3️⃣ Fazendo login como user..."
USER_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "user123"}')

USER_TOKEN=$(echo $USER_RESPONSE | jq -r '.access_token')

if [ "$USER_TOKEN" != "null" ] && [ -n "$USER_TOKEN" ]; then
  echo "✅ Login user bem-sucedido"
else
  echo "❌ Falha no login user"
fi
echo ""

# 4. Listar tintas (público)
echo "4️⃣ Listando tintas (endpoint público)..."
PAINTS_COUNT=$(curl -s "$API_URL/paints" | jq '. | length')
echo "✅ Encontradas $PAINTS_COUNT tintas"
echo ""

# 5. Criar tinta como Admin
echo "5️⃣ Criando tinta como admin..."
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/paints" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tinta Teste Admin",
    "description": "Tinta criada via teste",
    "color_code": "TEST001",
    "environment": "INTERIOR",
    "finish_type": "FOSCO",
    "line": "STANDARD"
  }')

PAINT_ID=$(echo $CREATE_RESPONSE | jq -r '.id')

if [ "$PAINT_ID" != "null" ] && [ -n "$PAINT_ID" ]; then
  echo "✅ Tinta criada com sucesso (ID: $PAINT_ID)"
else
  echo "❌ Falha ao criar tinta"
  echo "Resposta: $CREATE_RESPONSE"
fi
echo ""

# 6. Tentar criar tinta como User (deve falhar)
echo "6️⃣ Tentando criar tinta como user (deve falhar)..."
USER_CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/paints" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tinta Teste User",
    "description": "Tinta criada por user",
    "color_code": "TEST002",
    "environment": "INTERIOR",
    "finish_type": "FOSCO",
    "line": "STANDARD"
  }')

HTTP_CODE=$(echo "$USER_CREATE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "403" ]; then
  echo "✅ Permissão negada corretamente (403 Forbidden)"
else
  echo "❌ Erro: Esperado 403, recebido $HTTP_CODE"
fi
echo ""

# 7. Chat sem autenticação
echo "7️⃣ Testando chat sem autenticação..."
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, teste"}')

CHAT_MESSAGE=$(echo $CHAT_RESPONSE | jq -r '.response')

if [ -n "$CHAT_MESSAGE" ]; then
  echo "✅ Chat funcionando sem autenticação"
  echo "Resposta: ${CHAT_MESSAGE:0:100}..."
else
  echo "❌ Falha no chat"
fi
echo ""

# 8. Chat com autenticação
echo "8️⃣ Testando chat com autenticação (admin)..."
AUTH_CHAT_RESPONSE=$(curl -s -X POST "$API_URL/ai/chat" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, teste autenticado"}')

AUTH_CHAT_MESSAGE=$(echo $AUTH_CHAT_RESPONSE | jq -r '.response')

if [ -n "$AUTH_CHAT_MESSAGE" ]; then
  echo "✅ Chat funcionando com autenticação"
  echo "Resposta: ${AUTH_CHAT_MESSAGE:0:100}..."
else
  echo "❌ Falha no chat autenticado"
fi
echo ""

# 9. Limpar tinta de teste (se foi criada)
if [ "$PAINT_ID" != "null" ] && [ -n "$PAINT_ID" ]; then
  echo "9️⃣ Deletando tinta de teste..."
  DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/paints/$PAINT_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")
  
  HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)
  
  if [ "$HTTP_CODE" == "204" ]; then
    echo "✅ Tinta de teste deletada"
  else
    echo "⚠️ Não foi possível deletar tinta de teste"
  fi
  echo ""
fi

echo "✅ Todos os testes concluídos!"
echo ""
echo "📚 Acesse a documentação em: $API_URL/docs"

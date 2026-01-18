#!/bin/bash
# =============================================================================
# SUVINIL AI - Script de Teste da API
# =============================================================================
# Este script testa todos os endpoints da API do assistente inteligente
# 
# Uso:
#   chmod +x test_api.sh
#   ./test_api.sh
# =============================================================================

# Configurações
BASE_URL="${BASE_URL:-http://localhost:8000}"
USERNAME="${USERNAME:-admin}"
PASSWORD="${PASSWORD:-admin123}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0

# Função para imprimir cabeçalhos
print_header() {
    echo -e "\n${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}==============================================================================${NC}\n"
}

# Função para verificar resposta
check_response() {
    local response="$1"
    local expected_field="$2"
    local test_name="$3"
    
    if echo "$response" | grep -q "$expected_field"; then
        echo -e "${GREEN}✓ PASSOU: $test_name${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FALHOU: $test_name${NC}"
        echo -e "${RED}  Resposta: $response${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# =============================================================================
# INÍCIO DOS TESTES
# =============================================================================

print_header "SUVINIL AI - Testes da API"
echo "Base URL: $BASE_URL"
echo "Usuário: $USERNAME"

# -----------------------------------------------------------------------------
# 1. Health Check
# -----------------------------------------------------------------------------
print_header "1. Health Check"

response=$(curl -s "$BASE_URL/health")
check_response "$response" "healthy" "Health check"
echo "Resposta: $response"

# -----------------------------------------------------------------------------
# 2. Root Endpoint
# -----------------------------------------------------------------------------
print_header "2. Root Endpoint"

response=$(curl -s "$BASE_URL/")
check_response "$response" "Suvinil AI API" "Root endpoint"
echo "Resposta: $response"

# -----------------------------------------------------------------------------
# 3. Autenticação - Login
# -----------------------------------------------------------------------------
print_header "3. Autenticação - Login"

response=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$USERNAME&password=$PASSWORD")

check_response "$response" "access_token" "Login com credenciais válidas"

# Extrair token
TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
    echo -e "${RED}ERRO: Não foi possível obter token. Encerrando testes.${NC}"
    exit 1
fi

echo -e "${GREEN}Token obtido com sucesso!${NC}"
echo "Token: ${TOKEN:0:50}..."

# -----------------------------------------------------------------------------
# 4. Verificar Usuário Atual
# -----------------------------------------------------------------------------
print_header "4. Verificar Usuário Atual"

response=$(curl -s -X GET "$BASE_URL/users/me" \
    -H "Authorization: Bearer $TOKEN")

check_response "$response" "username" "Obter dados do usuário atual"
echo "Resposta: $response"

# -----------------------------------------------------------------------------
# 5. Listar Tintas
# -----------------------------------------------------------------------------
print_header "5. Listar Tintas"

response=$(curl -s -X GET "$BASE_URL/paints?limit=5" \
    -H "Authorization: Bearer $TOKEN")

check_response "$response" "name" "Listar tintas"
echo "Primeiros 200 caracteres: ${response:0:200}..."

# -----------------------------------------------------------------------------
# 6. Status do Serviço de IA
# -----------------------------------------------------------------------------
print_header "6. Status do Serviço de IA"

response=$(curl -s -X GET "$BASE_URL/ai/status")
check_response "$response" "service" "Status do serviço de IA"
echo "Resposta: $response"

# -----------------------------------------------------------------------------
# 7. Chat com IA - Saudação
# -----------------------------------------------------------------------------
print_header "7. Chat com IA - Saudação"

response=$(curl -s -X POST "$BASE_URL/ai/chat" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Olá! Preciso de ajuda para escolher uma tinta."}')

check_response "$response" "response" "Chat - saudação"
echo "Resposta: $(echo $response | head -c 300)..."

# -----------------------------------------------------------------------------
# 8. Chat com IA - Busca por ambiente
# -----------------------------------------------------------------------------
print_header "8. Chat com IA - Busca por Ambiente"

response=$(curl -s -X POST "$BASE_URL/ai/chat" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Quero pintar meu quarto, preciso de algo fácil de limpar e sem cheiro forte."}')

check_response "$response" "response" "Chat - busca por ambiente interno"
echo "Resposta: $(echo $response | head -c 400)..."

# -----------------------------------------------------------------------------
# 9. Chat com IA - Busca externa
# -----------------------------------------------------------------------------
print_header "9. Chat com IA - Busca para Exterior"

response=$(curl -s -X POST "$BASE_URL/ai/chat" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Preciso pintar a fachada da minha casa. Bate muito sol e chove bastante."}')

check_response "$response" "response" "Chat - busca para exterior"
echo "Resposta: $(echo $response | head -c 400)..."

# -----------------------------------------------------------------------------
# 10. Chat com IA - Busca por característica
# -----------------------------------------------------------------------------
print_header "10. Chat com IA - Busca por Característica"

response=$(curl -s -X POST "$BASE_URL/ai/chat" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Tem tinta para madeira que seja resistente ao calor?"}')

check_response "$response" "response" "Chat - busca por característica"
echo "Resposta: $(echo $response | head -c 400)..."

# -----------------------------------------------------------------------------
# 11. Chat com IA - Sugestão de cor
# -----------------------------------------------------------------------------
print_header "11. Chat com IA - Sugestão de Cor"

response=$(curl -s -X POST "$BASE_URL/ai/chat" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Quero pintar meu escritório com um tom de cinza moderno."}')

check_response "$response" "response" "Chat - sugestão de cor"
echo "Resposta: $(echo $response | head -c 400)..."

# -----------------------------------------------------------------------------
# 12. Histórico de Chat
# -----------------------------------------------------------------------------
print_header "12. Histórico de Chat"

response=$(curl -s -X GET "$BASE_URL/ai/chat/history?limit=10" \
    -H "Authorization: Bearer $TOKEN")

check_response "$response" "messages" "Obter histórico de chat"
echo "Resposta: $(echo $response | head -c 200)..."

# -----------------------------------------------------------------------------
# 13. Resetar Chat
# -----------------------------------------------------------------------------
print_header "13. Resetar Chat"

response=$(curl -s -X POST "$BASE_URL/ai/chat/reset" \
    -H "Authorization: Bearer $TOKEN")

check_response "$response" "message" "Resetar conversa"
echo "Resposta: $response"

# -----------------------------------------------------------------------------
# 14. Filtrar Tintas por Ambiente
# -----------------------------------------------------------------------------
print_header "14. Filtrar Tintas por Ambiente"

response=$(curl -s -X GET "$BASE_URL/paints?environment=interno&limit=5" \
    -H "Authorization: Bearer $TOKEN")

check_response "$response" "name" "Filtrar tintas por ambiente interno"
echo "Primeiros 200 caracteres: ${response:0:200}..."

# -----------------------------------------------------------------------------
# 15. Buscar Tinta por ID
# -----------------------------------------------------------------------------
print_header "15. Buscar Tinta por ID"

response=$(curl -s -X GET "$BASE_URL/paints/1" \
    -H "Authorization: Bearer $TOKEN")

check_response "$response" "name" "Buscar tinta por ID"
echo "Resposta: $response"

# =============================================================================
# RESUMO DOS TESTES
# =============================================================================
print_header "RESUMO DOS TESTES"

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
echo -e "Total de testes: $TOTAL"
echo -e "${GREEN}Passou: $TESTS_PASSED${NC}"
echo -e "${RED}Falhou: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ TODOS OS TESTES PASSARAM!${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠ Alguns testes falharam. Verifique os logs acima.${NC}"
    exit 1
fi

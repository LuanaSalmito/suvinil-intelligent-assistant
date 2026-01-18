#!/bin/bash

# Script para iniciar toda a aplicação com Docker
# Uso: ./start-docker.sh

set -e

echo "🐳 Iniciando Suvinil AI com Docker"
echo "=================================="
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado"
    echo "Por favor, instale Docker primeiro: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose não está instalado"
    echo "Por favor, instale Docker Compose primeiro"
    exit 1
fi

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "📝 Criando .env a partir do .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "⚠️  Por favor, edite o arquivo .env com suas configurações"
    else
        echo "⚠️  Arquivo .env.example não encontrado. Criando .env básico..."
        cat > .env << EOF
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=suvinil_db

# Backend
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
OPENAI_API_KEY=

# Frontend
VITE_API_URL=http://localhost:8000
EOF
    fi
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down 2>/dev/null || true

# Build e iniciar
echo "🔨 Fazendo build das imagens..."
docker-compose build

echo "🚀 Iniciando containers..."
docker-compose up -d

echo ""
echo "⏳ Aguardando serviços iniciarem..."
sleep 10

# Verificar saúde dos serviços
echo ""
echo "🔍 Verificando saúde dos serviços..."

# Verificar PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL está rodando"
else
    echo "⚠️  PostgreSQL ainda não está pronto"
fi

# Verificar Backend
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend está rodando"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend não está respondendo (pode estar inicializando)"
        echo "   Verifique os logs: docker-compose logs backend"
    fi
    sleep 1
done

# Verificar Frontend
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo "✅ Frontend está rodando"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Frontend não está respondendo (pode estar inicializando)"
        echo "   Verifique os logs: docker-compose logs frontend"
    fi
    sleep 1
done

echo ""
echo "✅ Aplicação iniciada!"
echo ""
echo "📍 URLs:"
echo "   - Frontend:    http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - Swagger:     http://localhost:8000/docs"
echo "   - PostgreSQL:  localhost:5432"
echo ""
echo "📋 Comandos úteis:"
echo "   - Ver logs:    docker-compose logs -f"
echo "   - Parar:       docker-compose down"
echo "   - Reiniciar:   docker-compose restart"
echo ""

#!/bin/bash

# Script para rodar a aplicação localmente

echo "🚀 Iniciando Suvinil AI API..."

# Verificar se existe venv
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar venv
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📥 Instalando dependências..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Verificar se PostgreSQL está rodando (opcional)
echo ""
echo "⚠️  Certifique-se de que o PostgreSQL está rodando e configurado!"
echo "   DATABASE_URL: postgresql://postgres:postgres@localhost:5432/suvinil_db"
echo ""

# Inicializar banco (se necessário)
if [ "$1" == "--init-db" ]; then
    echo "🗄️  Inicializando banco de dados..."
    python -m app.core.init_db
fi

# Rodar aplicação
echo "🌐 Iniciando servidor..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000

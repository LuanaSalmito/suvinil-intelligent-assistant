# 🐳 Docker Setup - Suvinil AI

## 🚀 Início Rápido

### Desenvolvimento

```bash
# Na raiz do projeto
docker-compose up -d
```

Isso vai subir:
- ✅ PostgreSQL (porta 5432)
- ✅ Backend FastAPI (porta 8000)
- ✅ Frontend React (porta 5173)

### Acessar

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

## 📋 Comandos Úteis

### Iniciar tudo
```bash
docker-compose up -d
```

### Ver logs
```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Apenas frontend
docker-compose logs -f frontend
```

### Parar tudo
```bash
docker-compose down
```

### Parar e remover volumes (⚠️ apaga dados)
```bash
docker-compose down -v
```

### Rebuild após mudanças
```bash
# Rebuild e reiniciar
docker-compose up -d --build

# Apenas rebuild de um serviço
docker-compose build backend
docker-compose up -d backend
```

### Executar comandos dentro dos containers

```bash
# Backend
docker-compose exec backend bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.core.init_db

# Frontend
docker-compose exec frontend npm install
docker-compose exec frontend npm run build

# PostgreSQL
docker-compose exec postgres psql -U postgres -d suvinil_db
```

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=suvinil_db

# Backend
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
OPENAI_API_KEY=your-openai-api-key

# Frontend
VITE_API_URL=http://localhost:8000
```

### Ajustar Portas

Se precisar mudar as portas, edite `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8000:8000"  # Mude o primeiro número (host:container)
  
  frontend:
    ports:
      - "5173:5173"  # Mude o primeiro número (host:container)
```

## 🏭 Produção

### Build para Produção

```bash
# Usar docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d --build
```

**Diferenças na produção:**
- Frontend é buildado e servido via Nginx (porta 80)
- Backend roda sem `--reload`
- Variáveis de ambiente devem ser configuradas no `.env`

## 🐛 Troubleshooting

### Backend não inicia

```bash
# Ver logs
docker-compose logs backend

# Verificar se PostgreSQL está rodando
docker-compose ps

# Verificar conexão com banco
docker-compose exec backend python -c "from app.core.database import engine; engine.connect()"
```

### Frontend não conecta ao backend

1. Verificar se backend está rodando:
```bash
curl http://localhost:8000/health
```

2. Verificar variável de ambiente:
```bash
docker-compose exec frontend env | grep VITE_API_URL
```

3. Ajustar `VITE_API_URL` no `.env` ou `docker-compose.yml`

### Erro de permissão

```bash
# Dar permissão aos scripts
chmod +x suvinil-ai/test_api.sh
```

### Limpar tudo e começar de novo

```bash
# Parar e remover tudo
docker-compose down -v

# Remover imagens
docker-compose down --rmi all

# Limpar sistema Docker (cuidado!)
docker system prune -a
```

## 📁 Estrutura

```
.
├── docker-compose.yml          # Desenvolvimento
├── docker-compose.prod.yml     # Produção
├── .env                        # Variáveis de ambiente
├── suvinil-ai/
│   ├── Dockerfile              # Backend
│   └── ...
└── suvinil-frontend/
    ├── Dockerfile              # Frontend (dev)
    ├── Dockerfile.prod         # Frontend (prod)
    └── ...
```

## ✅ Checklist

- [ ] Docker e Docker Compose instalados
- [ ] Arquivo `.env` configurado
- [ ] Portas 8000, 5173 e 5432 disponíveis
- [ ] `docker-compose up -d` executado
- [ ] Backend acessível em http://localhost:8000/health
- [ ] Frontend acessível em http://localhost:5173

## 🎯 Próximos Passos

1. Acesse http://localhost:5173
2. Crie uma conta ou faça login
3. Teste o chatbot
4. Se for admin, teste o painel de administração

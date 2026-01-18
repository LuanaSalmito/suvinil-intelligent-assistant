# 🚀 Como Rodar e Testar a Aplicação

## Pré-requisitos

- Python 3.11+
- Node.js 18+
- PostgreSQL (ou usar Docker)
- Docker e Docker Compose (opcional, mas recomendado)

## Opção 1: Rodar com Docker (Recomendado) 🐳

### 1. Configurar variáveis de ambiente

```bash
cd suvinil-ai
cp .env.example .env
# Edite o .env se necessário
```

### 2. Subir os serviços

```bash
docker-compose up -d
```

Isso vai:
- ✅ Criar banco PostgreSQL
- ✅ Rodar migrações do Alembic
- ✅ Inicializar dados de exemplo
- ✅ Subir a API FastAPI na porta 8000

### 3. Verificar se está rodando

```bash
# Ver logs
docker-compose logs -f

# Verificar saúde da API
curl http://localhost:8000/health
```

### 4. Acessar documentação

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Opção 2: Rodar Manualmente (Desenvolvimento) 💻

### Backend (Python/FastAPI)

#### 1. Criar ambiente virtual

```bash
cd suvinil-ai
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

#### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

#### 3. Configurar banco de dados

```bash
# Criar banco PostgreSQL
createdb suvinil_db

# Ou usar Docker apenas para o banco
docker run -d \
  --name suvinil-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=suvinil_db \
  -p 5432:5432 \
  postgres:15
```

#### 4. Configurar .env

```bash
cp .env.example .env
# Edite o .env com suas configurações
```

#### 5. Rodar migrações

```bash
alembic upgrade head
```

#### 6. Inicializar dados

```bash
python -m app.core.init_db
```

#### 7. Rodar servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React/Vite)

#### 1. Instalar dependências

```bash
cd suvinil-frontend
npm install
```

#### 2. Configurar variáveis (opcional)

```bash
# Criar .env se necessário
echo "VITE_API_URL=http://localhost:8000" > .env
```

#### 3. Rodar servidor de desenvolvimento

```bash
npm run dev
```

Frontend estará em: http://localhost:5173

## 🧪 Testando a Aplicação

### 1. Testar Backend (API)

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Login como Admin
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Resposta esperada:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Usar o token para acessar endpoints protegidos

```bash
TOKEN="seu_token_aqui"

# Listar tintas (público)
curl http://localhost:8000/paints

# Criar tinta (requer admin)
curl -X POST http://localhost:8000/paints \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tinta Teste",
    "description": "Descrição teste",
    "color_code": "T001",
    "environment": "INTERIOR",
    "finish_type": "FOSCO",
    "line": "STANDARD"
  }'

# Chat com IA (funciona sem autenticação)
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, quais tintas você tem?"}'
```

### 2. Testar Frontend

#### Acessar aplicação
1. Abra http://localhost:5173
2. Você deve ver o chatbot diretamente

#### Testar Login
1. Clique em "Entrar" no header
2. Use credenciais:
   - **Admin**: `admin` / `admin123`
   - **User**: `user` / `user123`

#### Testar Chat
1. Digite uma mensagem no chat
2. Verifique se recebe resposta da IA

#### Testar Admin (apenas se logado como admin)
1. Faça login como admin
2. Clique em "Admin" no header
3. Teste criar, editar e deletar tintas

### 3. Testar Autenticação e RBAC

#### Teste 1: Usuário comum não pode criar tinta
```bash
# Login como user
USER_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "user123"}' | jq -r '.access_token')

# Tentar criar tinta (deve falhar com 403)
curl -X POST http://localhost:8000/paints \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Teste"}'
# Esperado: 403 Forbidden
```

#### Teste 2: Admin pode criar tinta
```bash
# Login como admin
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

# Criar tinta (deve funcionar)
curl -X POST http://localhost:8000/paints \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tinta Admin",
    "description": "Criada por admin",
    "color_code": "A001",
    "environment": "INTERIOR",
    "finish_type": "FOSCO",
    "line": "STANDARD"
  }'
# Esperado: 201 Created
```

## 📋 Checklist de Testes

### Backend
- [ ] API está rodando (health check)
- [ ] Swagger UI acessível
- [ ] Login funciona
- [ ] Token JWT é gerado corretamente
- [ ] Endpoints públicos funcionam sem token
- [ ] Endpoints protegidos requerem token
- [ ] Admin pode criar/editar/deletar tintas
- [ ] User comum NÃO pode criar/editar/deletar tintas
- [ ] Chat funciona com e sem autenticação

### Frontend
- [ ] Frontend está rodando
- [ ] Chat aparece na página inicial
- [ ] Login funciona
- [ ] Logout funciona
- [ ] Botão Admin aparece apenas para admins
- [ ] Página Admin funciona (criar/editar/deletar)
- [ ] Mensagens do chat são exibidas corretamente

## 🐛 Troubleshooting

### Backend não inicia

**Erro: Database connection failed**
```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Verificar variáveis de ambiente
cat suvinil-ai/.env
```

**Erro: Module not found**
```bash
# Reinstalar dependências
pip install -r requirements.txt
```

**Erro: Alembic migration failed**
```bash
# Resetar migrações (CUIDADO: apaga dados)
alembic downgrade base
alembic upgrade head
```

### Frontend não conecta ao backend

**Erro: CORS ou Network Error**
```bash
# Verificar se backend está rodando
curl http://localhost:8000/health

# Verificar URL no .env do frontend
cat suvinil-frontend/.env
```

### Login não funciona

**Verificar:**
1. Banco de dados tem usuários?
2. Usuário está ativo?
3. Token está sendo enviado corretamente?

```bash
# Verificar usuários no banco
docker exec -it suvinil-postgres psql -U postgres -d suvinil_db -c "SELECT username, role, is_active FROM users;"
```

## 📚 Documentação Adicional

- **Autenticação**: Ver `suvinil-ai/AUTHENTICATION.md`
- **API Docs**: http://localhost:8000/docs
- **Swagger**: http://localhost:8000/docs (interativo)

## 🎯 Próximos Passos

1. ✅ Testar todos os endpoints
2. ✅ Verificar permissões RBAC
3. ✅ Testar chat com e sem autenticação
4. ✅ Testar criação/edição de tintas como admin
5. ✅ Verificar que usuários comuns não podem modificar catálogo

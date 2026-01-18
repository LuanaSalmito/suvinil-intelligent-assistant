# 🎨 Suvinil AI - Catálogo Inteligente de Tintas com IA

Sistema assistente virtual especialista em tintas Suvinil, construído com FastAPI e IA (Langchain, RAG, Agentes).

## 📋 Sobre o Projeto

Este projeto implementa um **Assistente Inteligente** que atua como um especialista virtual em tintas, ajudando pessoas a escolherem o produto Suvinil ideal com base em contexto, dúvidas e preferências.

### Funcionalidades

- ✅ **CRUD de Tintas e Usuários** - API completa com autenticação JWT e RBAC
- ✅ **Chatbot Inteligente com IA** - Interpreta intenções e recomenda produtos adequados
- ✅ **RAG (Retrieval-Augmented Generation)** - Busca informações em tempo real no catálogo
- ✅ **Agentes com Ferramentas e Memória** - Sistema multi-agente com raciocínio e contexto
- ✅ **Embedding + Vector Store** - Usa ChromaDB para busca semântica de produtos
- ✅ **Swagger/OpenAPI** - Documentação interativa completa
- ✅ **Docker + Docker Compose** - Deploy fácil e isolado

## 🏗️ Arquitetura

O projeto segue **Clean Architecture** e **SOLID**, com separação de responsabilidades:

```
app/
├── api/v1/          # Endpoints FastAPI
├── core/            # Configurações e utilitários base
├── models/          # Modelos SQLAlchemy (banco de dados)
├── repositories/    # Camada de acesso a dados
├── schemas/         # Schemas Pydantic (validação)
├── services/        # Lógica de negócio (se necessário)
└── ai/              # Serviços de IA (RAG, Agentes)
```

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.11+
- PostgreSQL 15+ (ou Docker)
- OpenAI API Key (para serviços de IA)

### Opção 1: Com Docker (Recomendado)

```bash
# 1. Criar arquivo .env
cp .env.example .env
# Editar .env e adicionar sua OPENAI_API_KEY

# 2. Iniciar serviços
docker-compose up -d

# 3. Inicializar banco de dados
docker-compose exec api python -m app.core.init_db

# 4. Acessar
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Opção 2: Localmente (Sem Docker)

```bash
# 1. Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar PostgreSQL
# Criar banco: createdb suvinil_db
# Ou ajustar DATABASE_URL no .env

# 4. Criar arquivo .env
cp .env.example .env
# Editar .env e adicionar OPENAI_API_KEY e DATABASE_URL

# 5. Inicializar banco de dados
python -m app.core.init_db

# 6. Rodar aplicação
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 7. Acessar
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## 🧪 Como Testar

### 1. Testar sem autenticação (público)

```bash
# Health check
curl http://localhost:8000/health

# Listar tintas
curl http://localhost:8000/paints/

# Ver uma tinta específica
curl http://localhost:8000/paints/1
```

### 2. Testar com autenticação

#### Via Swagger UI (Mais fácil!)

1. Acesse http://localhost:8000/docs
2. Clique em `/auth/login`
3. Preencha:
   ```json
   {
     "username": "admin",
     "password": "admin123"
   }
   ```
4. Execute e copie o `access_token`
5. Clique no botão **"Authorize"** no topo
6. Cole: `Bearer <seu_token_aqui>`
7. Agora teste os endpoints protegidos!

#### Via cURL

```bash
# 1. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 2. Ver meu perfil
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer $TOKEN"

# 3. Chat com IA
curl -X POST "http://localhost:8000/ai/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "Quero pintar meu quarto, algo fácil de limpar e sem cheiro forte."}'
```

## 📚 Endpoints da API

### Autenticação
- `POST /auth/login` - Login e obter token JWT

### Usuários
- `GET /users/me` - Ver meu perfil (autenticado)
- `GET /users/` - Listar usuários (admin)
- `GET /users/{id}` - Ver usuário por ID
- `POST /users/` - Criar usuário (admin)
- `PUT /users/{id}` - Atualizar usuário
- `DELETE /users/{id}` - Deletar usuário (admin)

### Tintas
- `GET /paints/` - Listar tintas (público, com filtros)
- `GET /paints/{id}` - Ver tinta por ID (público)
- `POST /paints/` - Criar tinta (admin)
- `PUT /paints/{id}` - Atualizar tinta (admin)
- `DELETE /paints/{id}` - Deletar tinta (admin)

### IA Chat
- `POST /ai/chat` - Chat com assistente IA (autenticado)
- `POST /ai/chat/reset` - Resetar conversa (autenticado)

## 🤖 Funcionalidades de IA

### RAG (Retrieval-Augmented Generation)
- Usa **OpenAI Embeddings** para criar representações vetoriais das tintas
- **ChromaDB** como vector store para busca semântica
- Busca produtos relevantes baseado em intenção do usuário

### Agentes com Ferramentas
O agente utiliza três ferramentas principais:

1. **search_paints** - Busca tintas relevantes no catálogo
2. **get_paint_details** - Obtém detalhes completos de uma tinta
3. **list_all_paints** - Lista todas as tintas disponíveis

### Memória de Conversa
- Mantém contexto da conversa usando `ConversationBufferMemory`
- Permite conversas naturais e coerentes
- Possibilidade de resetar conversa

## 🗄️ Modelo de Dados

### Tinta (Paint)
- Nome, Cor, Nome da Cor
- Tipo de Superfície
- Ambiente (Interno/Externo/Ambos)
- Tipo de Acabamento (Fosco/Acetinado/Brilhante)
- Features (ex: lavável, anti-mofo, sem odor)
- Linha (Premium/Standard/Economy)
- Preço, Descrição

### Usuário (User)
- Email, Username, Senha (hash)
- Nome completo
- Role (Admin/User)
- Status ativo/inativo

## 🔐 Autenticação e RBAC

- **JWT (JSON Web Tokens)** para autenticação
- **RBAC (Role-Based Access Control)** com duas roles:
  - `admin` - Acesso completo (CRUD de usuários e tintas)
  - `user` - Acesso limitado (leitura de tintas, chat com IA)

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **PostgreSQL** - Banco de dados relacional
- **Pydantic** - Validação de dados
- **JWT** - Autenticação stateless

### IA
- **Langchain** - Framework para construção de aplicações com LLMs
- **OpenAI GPT-4o-mini** - Modelo de linguagem
- **OpenAI Embeddings** - Embeddings para RAG
- **ChromaDB** - Vector database para busca semântica

### DevOps
- **Docker** - Containerização
- **Docker Compose** - Orquestração de serviços
- **Alembic** - Migrations (preparado para uso)

## 📝 Exemplos de Uso do Chat

### Exemplo 1: Pintar quarto
**Usuário:**
```
Quero pintar meu quarto, mas prefiro algo que seja fácil de limpar e sem cheiro forte. Tem alguma sugestão?
```

**IA:**
```
Para ambientes internos como quartos, uma boa opção é a Suvinil Toque de Seda, que possui acabamento acetinado, é lavável e tem tecnologia sem odor.
```

### Exemplo 2: Fachada externa
**Usuário:**
```
Preciso pintar a fachada da minha casa. Bate muito sol e chove bastante por aqui. Qual tinta você recomenda?
```

**IA:**
```
Consultei nosso especialista em ambientes externos e o agente de resistência climática. Recomendamos a Suvinil Fachada Acrílica, que possui proteção contra chuva e sol, além de ser anti-mofo e lavável.
```

### Exemplo 3: Madeira resistente ao calor
**Usuário:**
```
Você tem alguma tinta para madeira que seja resistente ao calor?
```

**IA:**
```
Sim! A Suvinil Esmalte Sintético é ideal para madeira e resistente ao calor, além de ter acabamento brilhante. Deseja mais opções?
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/suvinil_db

# JWT
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# Application
ENVIRONMENT=development
DEBUG=True
```

## 🧪 Testes

Para executar testes (quando implementados):

```bash
pytest
```

## 📖 Documentação

A documentação interativa está disponível em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Uso de IA no Desenvolvimento

Este projeto foi desenvolvido usando ferramentas de IA para:

- **Cursor** - Edição contextual com IA
- **ChatGPT (OpenAI)** - Geração de código, brainstorming
- **Claude (Anthropic)** - Revisão técnica

### Exemplos de Prompts Utilizados

1. **Estrutura do Projeto:**
   ```
   Crie uma estrutura FastAPI seguindo Clean Architecture para um catálogo de tintas com autenticação JWT
   ```

2. **Serviço RAG:**
   ```
   Implemente um serviço RAG usando Langchain, ChromaDB e OpenAI Embeddings para buscar tintas no catálogo
   ```

3. **Agente com Ferramentas:**
   ```
   Crie um agente Langchain com ferramentas customizadas para buscar e recomendar tintas com memória de conversa
   ```

### Decisões Técnicas Baseadas em IA

- **Escolha do Langchain**: Sugerido para facilitar implementação de agentes e RAG
- **GPT-4o-mini**: Recomendado para balancear custo e qualidade
- **ChromaDB**: Sugerido como vector store leve e fácil de usar
- **Clean Architecture**: Seguido para manter código organizado e testável

## 📊 Próximos Passos

- [ ] Implementar testes unitários e de integração
- [ ] Adicionar geração de imagens com DALL·E (opcional)
- [ ] Implementar cache com Redis para sessões de agentes
- [ ] Adicionar logging estruturado
- [ ] Implementar métricas e observabilidade
- [ ] Adicionar rate limiting
- [ ] Melhorar tratamento de erros e validações
- [ ] Implementar migrations com Alembic

## 📄 Licença

Este projeto foi desenvolvido como desafio técnico.

## 👤 Autores

Desenvolvido com ❤️ usando IA generativa

---

**Nota**: Certifique-se de ter uma `OPENAI_API_KEY` válida configurada no arquivo `.env` para usar os serviços de IA.

# 🎨 Suvinil AI - Catálogo Inteligente de Tintas

Assistente Virtual Inteligente especializado em tintas Suvinil, construído com FastAPI, LangChain e OpenAI.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [API Endpoints](#api-endpoints)
- [Uso do Assistente IA](#uso-do-assistente-ia)
- [Ferramentas de IA Utilizadas](#ferramentas-de-ia-utilizadas)
- [Decisões Técnicas](#decisões-técnicas)

---

## 🎯 Visão Geral

O **Suvinil AI** é um assistente virtual que ajuda clientes a escolherem o produto Suvinil ideal para suas necessidades de pintura. A solução:

- ✅ Interpreta intenções do usuário em linguagem natural
- ✅ Busca e recomenda produtos usando RAG (Retrieval-Augmented Generation)
- ✅ Utiliza agente com ferramentas especializadas
- ✅ Mantém contexto da conversa (memória)
- ✅ Gera visualizações com DALL-E (opcional)
- ✅ Oferece API REST documentada com Swagger
- ✅ A geração visual foi considerada, mas priorizei a robustez do agente, RAG e arquitetura do backend dentro do prazo. Em um próximo ciclo, a imagem seria adicionada via DALL·E como ferramenta do agente

### Acompanhamento do backlog e de progresso

https://www.notion.so/Loomi-Back-IA-2eb19abb5799801a8b22d2f08a4e566e?source=copy_link


### Exemplos de Interação

```
Usuário: Quero pintar meu quarto, algo fácil de limpar e sem cheiro forte.
IA: Para ambientes internos como quartos, recomendo a **Suvinil Toque de Seda**, 
    que possui acabamento acetinado, é lavável e tem tecnologia sem odor...

Usuário: Preciso pintar a fachada da minha casa. Bate muito sol e chove bastante.
IA: Para fachadas expostas ao sol e chuva, recomendo a **Suvinil Fachada Premium** 
    com proteção UV e garantia de 15 anos contra descascamento...

Usuário: Como ficaria minha varanda de azul claro?
IA: Sugiro o tom **Azul Sereno** da linha Suvinil Fachada Acrílica. 
    [Gera visualização com DALL-E]
```

---

## 🏗 Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SUVINIL AI ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────────────────────────────────────┐    │
│  │   CLIENT    │───▶│              FastAPI (REST API)              │    │
│  │ (Swagger/   │    │  - Auth (JWT)                                │    │
│  │  Postman)   │◀───│  - CRUD Tintas/Usuários                      │    │
│  └─────────────┘    │  - Chat IA                                   │    │
│                     └─────────────────────────────────────────────┘    │
│                                       │                                 │
│                                       ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     AGENT SERVICE (LangChain)                    │   │
│  │                                                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                    SYSTEM PROMPT                          │   │   │
│  │  │  Especialista Suvinil + Regras + Exemplos                 │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │                              │                                   │   │
│  │  ┌───────────────────────────┴───────────────────────────┐      │   │
│  │  │                    TOOLS (8 ferramentas)               │      │   │
│  │  ├───────────────────────────────────────────────────────┤      │   │
│  │  │ • search_paints (RAG)      • compare_paints            │      │   │
│  │  │ • filter_by_environment    • suggest_colors            │      │   │
│  │  │ • filter_by_features       • generate_visualization    │      │   │
│  │  │ • get_paint_details        • list_all_paints           │      │   │
│  │  └───────────────────────────────────────────────────────┘      │   │
│  │                              │                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │              MEMORY (ConversationBufferWindow)            │   │   │
│  │  │              + Persistência em PostgreSQL                 │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      RAG SERVICE (ChromaDB)                      │   │
│  │  • Embeddings: text-embedding-3-small                           │   │
│  │  • Vector Store: ChromaDB                                       │   │
│  │  • Busca semântica por similaridade                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    │
│  │   PostgreSQL    │    │     OpenAI      │    │    DALL-E 3     │    │
│  │ (Dados + Chat)  │    │  (GPT-4o-mini)  │    │  (Visualização) │    │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tecnologias

### Backend
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **PostgreSQL** - Banco de dados relacional
- **Alembic** - Migrations de banco de dados

### Inteligência Artificial
- **LangChain** - Framework para aplicações com LLMs
- **OpenAI GPT-4o-mini** - Modelo de linguagem
- **OpenAI Embeddings** - Vetorização de texto
- **ChromaDB** - Vector store para RAG
- **DALL-E 3** - Geração de imagens (opcional)

### Infraestrutura
- **Docker** + **Docker Compose** - Containerização
- **JWT** - Autenticação
- **Swagger/OpenAPI** - Documentação da API

---

## 📦 Instalação

### Pré-requisitos
- Python
- PostgreSQL
- Docker

### 1. Clone o repositório
```bash
git clone <repository-url>
cd suvinil-ai
```

### 2. Crie ambiente virtual
```bash
python -m venv venv
source venv/bin/activate 
.\venv\Scripts\activate   
```

### 3. Instale dependências
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### 1. Crie arquivo `.env`
```bash
cp .env.example .env
```

### 2. Configure as variáveis
```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/suvinil_db

# JWT
SECRET_KEY=sua-chave-secreta-aqui-min-32-caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI (OBRIGATÓRIO para IA completa)
OPENAI_API_KEY=sk-your-openai-api-key

# Environment
ENVIRONMENT=development
DEBUG=True
```

### 3. Crie o banco de dados
```bash
createdb suvinil_db
# ou via Docker:
docker-compose up -d db
```

---

## 🚀 Execução

### Docker Compose
```bash
docker-compose up --build
```

### Seed do banco de dados
```bash
cd seed-db
```
- **Basta executar a seed que irá popular o banco com o csv**

### Acessar a API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📡 API Endpoints

### Autenticação
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/auth/login` | Login (retorna JWT token) |
| POST | `/auth/register` | Registrar novo usuário |

### Usuários
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/users/me` | Dados do usuário atual |
| GET | `/users` | Listar usuários (admin) |

### Tintas (CRUD)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/paints` | Listar tintas (com filtros) |
| GET | `/paints/{id}` | Detalhes de uma tinta |
| POST | `/paints` | Criar tinta (admin) |
| PUT | `/paints/{id}` | Atualizar tinta (admin) |
| DELETE | `/paints/{id}` | Deletar tinta (admin) |

### Chat IA
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/ai/chat` | Enviar mensagem para o assistente |
| POST | `/ai/chat/reset` | Resetar conversa |
| GET | `/ai/chat/history` | Obter histórico de mensagens |
| DELETE | `/ai/chat/history` | Limpar histórico |
| GET | `/ai/status` | Status do serviço de IA |

---

## 🤖 Uso do Assistente IA

### Exemplo de Request
```bash
curl -X POST "http://localhost:8000/ai/chat" \
  -H "Authorization: Bearer <seu-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Quero pintar meu quarto, algo lavável e sem odor"}'
```

### Exemplo de Response
```json
{
  "response": "Para ambientes internos como quartos, recomendo a **Suvinil Toque de Seda**...",
  "tools_used": [
    {"tool": "search_paints", "input": "quarto lavável sem odor interno"}
  ],
  "paints_mentioned": [1, 2, 3],
  "metadata": {
    "execution_time_ms": 1523.5,
    "intermediate_steps_count": 2,
    "model": "gpt-4o-mini",
    "mode": "ai"
  }
}
```

### Ferramentas do Agente

| Ferramenta | Descrição |
|------------|-----------|
| `search_paints` | Busca semântica de tintas (RAG) |
| `filter_by_environment` | Filtra por interno/externo |
| `filter_by_features` | Filtra por características |
| `get_paint_details` | Detalhes de uma tinta |
| `compare_paints` | Compara múltiplas tintas |
| `suggest_colors` | Sugere cores por estilo |
| `generate_visualization` | Gera imagem com DALL-E |
| `list_all_paints` | Lista catálogo completo |

---

## 🧰 Ferramentas de IA Utilizadas

### Desenvolvimento
- **Cursor** - IDE com IA para desenvolvimento contextual
- **Claude (Anthropic)** - Revisão de código e arquitetura

### Na Aplicação
- **OpenAI GPT-4o-mini** - Modelo de linguagem principal
- **OpenAI Embeddings** - Vetorização para busca semântica
- **DALL-E 3** - Geração de visualizações

### Exemplos de Prompts Utilizados

**System Prompt do Agente:**
```
Você é um Assistente Virtual Especialista em Tintas Suvinil...
[Personalidade definida + Responsabilidades + Regras + Exemplos]
```

**Prompt para Geração de Imagem:**
```
Create a photorealistic interior/exterior design visualization 
of a {environment} painted with {color} color paint...
```

---

## 📊 Decisões Técnicas

### 1. LangChain + OpenAI Tools Agent
**Por quê**: Framework maduro que facilita a criação de agentes com ferramentas, memória e observabilidade.

### 2. RAG com ChromaDB
**Por quê**: Busca semântica permite encontrar tintas mesmo quando o usuário não usa termos exatos. ChromaDB é leve e fácil de usar localmente.

### 3. GPT-4o-mini vs GPT-4
**Por quê**: Bom equilíbrio entre qualidade e custo. Suficiente para recomendações de tintas com baixa latência.

### 4. Memória com Janela Deslizante
**Por quê**: Mantém as últimas 10 interações para contexto sem custo excessivo de tokens.

### 5. Fallback sem IA
**Por quê**: API funciona mesmo sem OpenAI configurada, usando busca por palavras-chave como fallback.

### 6. Catálogo Enriquecido
**Por quê**: Base de dados expandida com 40+ produtos para demonstrar capacidade do RAG.

---

## 🔜 Próximos Passos

1. **Cache Redis** - Armazenar sessões de agentes em Redis para escalabilidade
2. **Streaming** - Respostas em streaming para melhor UX
3. **Multi-tenancy** - Suporte a múltiplos clientes/marcas
4. **Analytics** - Dashboard de uso e satisfação
5. **Testes automatizados** - Cobertura de testes unitários e integração

---

## 📄 Licença

Este projeto foi desenvolvido como parte de um desafio técnico.

---

## 👨‍💻 Autor

Desenvolvido com ❤️ para o desafio Loomi Backend IA.

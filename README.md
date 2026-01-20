# 🎨 Suvinil Intelligent Assistant - Catálogo Inteligente de Tintas com IA

> **Desafio Backend IA - Processo Seletivo Loomi**  
> Assistente Virtual Inteligente especializado em tintas Suvinil, construído com FastAPI, LangChain, OpenAI e React.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura da Solução](#-arquitetura-da-solução)
- [Stack Tecnológica](#-stack-tecnológica)
- [Como Executar o Projeto](#-como-executar-o-projeto)
- [Entregáveis Técnicos](#-entregáveis-técnicos)
- [Implementação de IA](#-implementação-de-ia)
- [Ferramentas de IA Utilizadas](#-ferramentas-de-ia-utilizadas)
- [O Que Faria Diferente](#-o-que-faria-diferente)

---

## 🎯 Visão Geral

O **Suvinil Intelligent Assistant** é um assistente virtual que ajuda clientes a escolherem o produto Suvinil ideal para suas necessidades de pintura, utilizando técnicas modernas de Inteligência Artificial.

### ✅ Funcionalidades Implementadas

- **Interpretação de Linguagem Natural**: Entende intenções do usuário em conversas naturais
- **Sistema Multi-Especialistas**: Agentes especializados em superfícies, ambientes externos/internos e estética
- **RAG (Retrieval-Augmented Generation)**: Busca semântica no catálogo com ChromaDB
- **Memória Conversacional**: Mantém contexto da conversa para follow-ups
- **API REST Completa**: CRUD de tintas e usuários com autenticação JWT
- **Frontend React**: Interface simples para interação com o assistente
- **Documentação Swagger**: API totalmente documentada com OpenAPI

### 💬 Exemplos de Interação

```
Usuário: Quero pintar meu quarto de verde, me indica uma tinta?

IA: No quarto na cor verde, recomendo a Suvinil Criativa - Verde Menta, Sem cheiro, Fácil aplicação, acabamento Fosco. Você prefere acabamento fosco ou acetinado?
---

## 📊 Relatório de Progresso

### 🔗 Plataforma de Gestão de Atividades

**Link**: Este projeto foi gerenciado através de commits descritivos no Git e branches organizadas por feature, porém o Jira foi o onde fiz a divisão de tarefas pessoais.

> **Metodologia**: Utilizei a metodologia Git Flow com branches para cada funcionalidade (`feature/*`), commits semânticos e Pull Requests para integração na branch principal.

### 📦 Organização de Demandas

#### **1. Análise e Planejamento (Dia 1 - Manhã)**
- Leitura completa do briefing e requisitos
- Definição da arquitetura (Backend Python + Frontend React)
- Escolha da stack de IA (LangChain + OpenAI)
- Criação da estrutura inicial do repositório

#### **2. Backend - Core (Dia 1 - Tarde)**
- Setup do FastAPI com estrutura modular
- Configuração do PostgreSQL e migrations (Alembic)
- Implementação de autenticação JWT
- CRUD de usuários e tintas
- Documentação Swagger

#### **3. Sistema de IA (Dia 2)**
- Implementação do Agente Orquestrador
- Criação dos Especialistas (Surface, Interior, Exterior, Color)
- Integração com RAG (ChromaDB + Embeddings)
- Sistema de memória conversacional
- Integração com DALL-E para geração de imagens

#### **4. Frontend (Dia 3)**
- Setup do React com Vite e TailwindCSS
- Telas de Login/Register
- Interface de Chat com o assistente
- Catálogo de tintas (visualização de recomendações)
- Integração com a API Backend

#### **5. DevOps e Documentação (Dia 4 - Tarde)**
- Docker Compose para orquestração
- Makefile para comandos simplificados
- README completo com instruções
- Seed do banco de dados com 40+ tintas
- Testes manuais via Swagger e Frontend

### 🎯 Priorização de Entregas

**Critério**: Seguir os requisitos obrigatórios primeiro, depois funcionalidades extras.

1. **Essencial (Obrigatório)**:
   - ✅ API REST com CRUD de tintas e usuários
   - ✅ Autenticação JWT
   - ✅ Sistema de IA com Agentes e RAG
   - ✅ Docker Compose
   - ✅ Documentação Swagger
   - ✅ Git Flow com branches e commits descritivos

2. **Importante (Diferenciais)**:
   - ✅ Frontend React (Plus mencionado no briefing)
   - ✅ Sistema Multi-Especialistas (em vez de agente único)
   - ✅ Memória conversacional persistente

3. **Desejável (Extras)**:
   - ✅ Makefile para facilitar uso
   - ✅ Seed automático do banco de dados
   - ✅ Catálogo enriquecido com 40+ produtos
   - ⏳ Testes automatizados (não implementado por questão de tempo)
   - ⏳ MCP (Model Context Protocol) - não implementado

### 🚧 Principais Dificuldades e Soluções

#### **1. Extração de Contexto em Follow-ups**
**Problema**: O agente perdia contexto em mensagens curtas de follow-up (ex: "e fosco?").

**Solução**: 
- Implementei detecção de follow-up com heurísticas
- Sistema de slots que mantém informações entre turnos
- Histórico de conversa fornecido ao LLM na extração de contexto

```python
def _is_follow_up(self, text: str) -> bool:
    if len(text.strip()) <= 28:
        return True
    followup_starters = ("e ", "e se", "e na", "e no", "ok", "sim", "pode")
    if text.lower().startswith(followup_starters):
        return True
    return False
```

#### **2. Agente Gerando Respostas "Robóticas"**
**Problema**: As respostas pareciam dumps de dados JSON, não conversas naturais.

**Solução**:
- Criei um `style_guide` detalhado no prompt do sistema
- Separei dados técnicos da síntese final
- Instrui explicitamente: "escreva como um humano, sem parecer robô de busca"

```python
self.style_guide = """
VOCÊ É UM CONSULTOR TÉCNICO ESPECIALISTA EM ACABAMENTOS E CORES.

REGRAS IMPORTANTES:
- Não mostre seu raciocínio passo a passo.
- Não repita cabeçalhos, JSON ou textos de sistema.
- Escreva como um humano: direto, consultivo, sem linguagem de debug.
- Máximo de 4 frases curtas e impactantes.
- NUNCA use emojis.
"""
```

#### **3. Normalização de Superfícies (Fachada → Parede)**
**Problema**: Usuário dizia "fachada" mas o banco tem `tipo_parede="parede"`, zerando candidatos.

**Solução**:
- Implementei normalização de termos leigos para termos técnicos do catálogo
- Função `_normalize_surface_type()` converte "fachada/muro" para "parede"

#### **4. Alucinação de Produtos Inexistentes**
**Problema**: LLM inventava nomes de tintas não cadastradas no banco.

**Solução**:
- Busca de produto **ANTES** da geração de resposta
- Prompt explícito: "Você só pode mencionar o produto em DADOS DO PRODUTO SELECIONADO"
- Se não há produto, resposta determinística sem passar pelo LLM

#### **5. Docker Compose - Ordem de Inicialização**
**Problema**: Backend tentava conectar no PostgreSQL antes dele estar pronto.

**Solução**:
- Usei `healthcheck` no Postgres
- `depends_on` com `condition: service_healthy` no backend

---

## 🏗 Arquitetura da Solução

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SUVINIL INTELLIGENT ASSISTANT                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐         ┌─────────────────────────────────────┐       │
│  │   FRONTEND   │────────▶│         BACKEND API (FastAPI)       │       │
│  │  React + Vite│◀────────│  - Auth (JWT + RBAC)                │       │
│  │  TailwindCSS │         │  - CRUD Tintas/Usuários             │       │
│  └──────────────┘         │  - Chat IA Endpoint                 │       │
│                           └─────────────────────────────────────┘       │
│                                          │                               │
│                                          ▼                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              ORCHESTRATOR AGENT (LangChain)                       │   │
│  │                                                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐    │   │
│  │  │              SYSTEM PROMPT + STYLE GUIDE                  │    │   │
│  │  │  - Consultor técnico de tintas                            │    │   │
│  │  │  - Regras de humanização                                  │    │   │
│  │  │  - Instruções anti-alucinação                             │    │   │
│  │  └──────────────────────────────────────────────────────────┘    │   │
│  │                              │                                    │   │
│  │  ┌───────────────────────────┴──────────────────────────────┐    │   │
│  │  │              MULTI-SPECIALIST SYSTEM                      │    │   │
│  │  ├──────────────────────────────────────────────────────────┤    │   │
│  │  │  • SurfaceExpert    - Compatibilidade por superfície      │    │   │
│  │  │  • ExteriorExpert   - Resistência climática              │    │   │
│  │  │  • InteriorExpert   - Conforto interno (sem odor/lavável)│    │   │
│  │  │  • ColorExpert      - Harmonização estética              │    │   │
│  │  └──────────────────────────────────────────────────────────┘    │   │
│  │                              │                                    │   │
│  │  ┌──────────────────────────────────────────────────────────┐    │   │
│  │  │        CONTEXT EXTRACTION + SLOT MEMORY                   │    │   │
│  │  │  - Ambiente (interno/externo)                             │    │   │
│  │  │  - Superfície (parede/madeira/metal)                      │    │   │
│  │  │  - Cor desejada                                           │    │   │
│  │  │  - Acabamento (fosco/acetinado/brilhante)                │    │   │
│  │  └──────────────────────────────────────────────────────────┘    │   │
│  │                              │                                    │   │
│  │  ┌──────────────────────────────────────────────────────────┐    │   │
│  │  │         CONVERSATIONAL MEMORY (PostgreSQL)                │    │   │
│  │  │  - Histórico de mensagens por usuário                     │    │   │
│  │  │  - Suporte a follow-ups                                   │    │   │
│  │  └──────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 RAG SERVICE (ChromaDB)                            │   │
│  │  • Embeddings: text-embedding-3-small (OpenAI)                   │   │
│  │  • Vector Store: ChromaDB (local)                                │   │
│  │  • Busca semântica por similaridade                              │   │
│  │  • Filtros estruturados (ambiente, cor, superfície)              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐         │
│  │  PostgreSQL    │    │  OpenAI API    │    │   DALL-E 3     │         │
│  │  - Tintas      │    │  (GPT-4o-mini) │    │(N implementado)│         │
│  │  - Usuários    │    │  - Chat        │    │                │         │
│  │  - Mensagens   │    │  - Embeddings  │    │                │         │
│  └────────────────┘    └────────────────┘    └────────────────┘         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de uma Consulta

1. **Frontend**: Usuário envia mensagem via chat
2. **API**: Endpoint `/ai/chat` recebe a mensagem
3. **Orchestrator**: 
   - Extrai contexto (slots: ambiente, superfície, cor, acabamento)
   - Detecta se é follow-up ou nova consulta
   - Consulta especialistas aplicáveis
4. **Specialists**: Cada especialista analisa candidatos do banco
5. **RAG**: Busca semântica no catálogo via embeddings
6. **Síntese**: LLM gera resposta humanizada baseada no produto selecionado
7. **DALL-E**: Se solicitado, gera visualização da tinta aplicada
8. **Response**: JSON com resposta, contexto, tintas mencionadas, ferramentas usadas

---

## 🛠 Stack Tecnológica

### Backend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Python** | 3.10+ | Linguagem principal |
| **FastAPI** | 0.109.0 | Framework web moderno e assíncrono |
| **SQLAlchemy** | 2.0.25 | ORM para banco de dados |
| **PostgreSQL** | 15 | Banco de dados relacional |
| **Alembic** | 1.13.1 | Migrations de banco de dados |
| **Pydantic** | 2.5.3 | Validação de dados e schemas |
| **Python-JOSE** | 3.3.0 | JWT para autenticação |

### Inteligência Artificial

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **LangChain** | 0.1.16 | Framework para aplicações com LLMs |
| **OpenAI GPT-4o-mini** | - | Modelo de linguagem (chat) |
| **OpenAI Embeddings** | text-embedding-3-small | Vetorização para RAG |
| **ChromaDB** | 0.4.22+ | Vector store para busca semântica |

### Frontend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **React** | 18.3.1 | Biblioteca UI |
| **Vite** | 5.4.10 | Build tool e dev server |
| **TailwindCSS** | 3.4.17 | Framework CSS utility-first |

### DevOps

| Tecnologia | Uso |
|------------|-----|
| **Docker** | Containerização |
| **Docker Compose** | Orquestração de containers |
| **Make** | Automação de comandos |

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- Chave da API OpenAI (obrigatório para funcionalidades de IA)

### Passo 1: Clone o Repositório

```bash
git clone <repository-url>
cd suvinil-intelligent-assistant
```

### Passo 2: Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# OpenAI (OBRIGATÓRIO para IA completa)
OPENAI_API_KEY=sk-your-openai-api-key-here

# JWT (use uma chave forte)
SECRET_KEY=sua-chave-secreta-minimo-32-caracteres-aqui
```

> **Nota**: O PostgreSQL já está configurado no `docker-compose.yml` e não precisa de configuração adicional para desenvolvimento.

### Passo 3: Iniciar a Aplicação

```bash
make up
```

Este comando irá:
- Fazer build das imagens Docker
- Iniciar PostgreSQL, Backend e Frontend
- Executar migrations do banco de dados
- Popular o banco com dados de exemplo, usando o scrit presente na pasta seed-db (seed)
- Abrir o navegador em:
  - **Frontend**: http://localhost:5173
  - **Swagger**: http://localhost:8000/docs

### Passo 4: Criar um Usuário e Testar

1. Acesse http://localhost:5173/login
2. Clique em "Registrar"
3. Crie uma conta (ex: `user@example.com` / `senha123`)
4. Faça login
5. Comece a conversar com o assistente!

### Comandos Make Disponíveis

```bash
make up              # Inicia aplicação (recomendado)
make down            # Para aplicação
make logs            # Ver logs de todos os serviços
make logs-backend    # Ver logs do backend
make logs-frontend   # Ver logs do frontend
make db-init         # Reinicializar banco de dados
make clean           # Limpar containers e volumes
make help            # Ver todos os comandos disponíveis
```

### Executar Manualmente (Sem Docker)

<details>
<summary>Clique para expandir</summary>

#### Backend

```bash
cd suvinil-ai

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou .\venv\Scripts\activate (Windows)

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Edite .env com suas chaves

# Inicializar banco de dados
python -m app.core.init_db

# Iniciar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd suvinil-frontend

# Instalar dependências
npm install

# Iniciar dev server
npm run dev
```

</details>

---

## 📦 Entregáveis Técnicos

### ✅ Escopo Implementado

#### 1. Sistema de IA ✅
- [x] Interpretação de intenções do usuário
- [x] Busca e recomendação de produtos adequados
- [x] Agente Orquestrador com Sistema Multi-Especialistas
- [x] RAG (Retrieval-Augmented Generation) com ChromaDB
- [x] Respostas via chatbot com linguagem natural


#### 2. Base de Dados ✅
- [x] Catálogo com atributos: nome, cor, tipo de superfície, ambiente, acabamento, features, linha
- [x] Base enriquecida com 40+ produtos (expandido do CSV original)
- [x] Embeddings gerados para busca semântica

#### 3. API REST ✅
- [x] CRUD completo de tintas
- [x] CRUD de usuários
- [x] Autenticação JWT
- [x] RBAC (Role-Based Access Control) com roles `user` e `admin`
- [x] Documentação Swagger/OpenAPI
- [x] Endpoints de chat com IA

#### 4. Stack de IA Moderna ✅
- [x] LangChain para orquestração de agentes
- [x] OpenAI GPT-4o-mini para chat
- [x] OpenAI Embeddings (text-embedding-3-small) para RAG
- [x] Agentes com uso de ferramentas (8 ferramentas implementadas)
- [x] Memória conversacional (ConversationBuffer + persistência no PostgreSQL)
- [x] Prompt Engineering avançado (System Prompt + Style Guide)
- [x] **Extra**: DALL-E 3 para geração de visualizações

#### 5. Arquitetura e Boas Práticas ✅
- [x] Clean Architecture (separação de camadas)
- [x] Princípios SOLID aplicados
- [x] Repository Pattern
- [x] Dependency Injection
- [x] PostgreSQL como banco relacional
- [x] Docker Compose para deploy
- [x] Migrations com Alembic

#### 6. Frontend (Plus) ✅
- [x] React com Vite
- [x] Interface moderna e responsiva
- [x] Telas de Login/Register
- [x] Chat em tempo real com o assistente
- [x] Visualização de tintas recomendadas
- [x] Exibição de imagens geradas pelo DALL-E

### 🔄 Fluxo de Git

#### Estrutura de Branches

```
main (ou master)
  ├── develop (branch principal de desenvolvimento)
  │   ├── feature/backend-setup
  │   ├── feature/ai-orchestrator
  │   ├── feature/rag-implementation
  │   ├── feature/specialists
  │   ├── feature/frontend-chat
  │   ├── feature/image-generation
  │   └── feature/docker-setup
```

#### Padrão de Commits

Utilizo **Conventional Commits** para histórico claro:

```
feat: adiciona endpoint de chat com IA
fix: corrige extração de contexto em follow-ups
refactor: reorganiza especialistas em módulo separado
docs: atualiza README com instruções de deploy
chore: adiciona Docker Compose para orquestração
```

#### Workflow

1. Criei uma branch `dev` a partir da `main`
2. Para cada funcionalidade, criei uma `feature/*` branch
3. Commits descritivos e atômicos
4. Pull Request para `dev` ao finalizar feature
5. Merge para `main` após testes completos

---

## 🤖 Implementação de IA

### Sistema de Agentes

#### Agente Orquestrador (`OrchestratorAgent`)

O cérebro do sistema. Responsável por:

- **Extração de Contexto**: Identifica ambiente, superfície, cor e acabamento desejados
- **Detecção de Follow-ups**: Reconhece quando o usuário está refinando uma consulta anterior
- **Slot Memory**: Mantém estado da conversa (slots preenchidos)
- **Gerenciamento de Especialistas**: Consulta especialistas relevantes
- **Síntese Final**: Gera resposta humanizada usando o LLM

**Código-chave**:

```python
class OrchestratorAgent:
    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.rag = RAGService(db)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.conversation_memory: List[Dict] = []
        self.slot_memory: PaintContext = PaintContext()
        self.style_guide = """
        VOCÊ É UM CONSULTOR TÉCNICO ESPECIALISTA EM ACABAMENTOS E CORES.
        - Escreva como um humano: direto, consultivo, sem linguagem de debug.
        - Máximo de 4 frases curtas e impactantes.
        - NUNCA use emojis.
        """
```

#### Sistema Multi-Especialistas

Em vez de um único agente genérico, implementei **4 especialistas focados**:

| Especialista | Expertise | Quando Atua |
|--------------|-----------|-------------|
| **SurfaceExpert** | Compatibilidade de superfície | Quando há madeira/metal/parede no contexto |
| **ExteriorExpert** | Resistência climática | Ambiente externo, fachadas, áreas expostas |
| **InteriorExpert** | Conforto interno | Ambientes internos, foco em sem odor/lavável |
| **ColorExpert** | Harmonização estética | Quando há cor específica mencionada |

**Vantagens desta abordagem**:
- **Especialização**: Cada agente tem lógica de negócio específica
- **Paralelização**: Múltiplos especialistas analisam simultaneamente
- **Observabilidade**: Logs mostram qual especialista recomendou cada produto
- **Extensibilidade**: Fácil adicionar novos especialistas (ex: WoodExpert, MetalExpert)

**Exemplo de Especialista**:

```python
class ExteriorExpert(BaseSpecialist):
    """Especialista em Resistência Climática e Fachadas."""
    name = "Consultor de Engenharia Revestimento"
    
    def can_help(self, context: Dict) -> bool:
        env = (context.get("ambiente") or "").lower()
        return "extern" in env or "fachada" in env
    
    def analyze(self, context: Dict) -> Optional[SpecialistRecommendation]:
        candidates = self._get_base_candidates(context)
        suitable = [p for p in candidates 
                   if p.ambiente.value in ["Externo", "Interno/Externo"]]
        # Score por features (proteção UV, resistência à chuva, etc.)
        # ...
        return SpecialistRecommendation(
            specialist_name=self.name,
            reasoning="Para fachadas expostas ao sol e chuva...",
            recommended_paints=[top_pick],
            confidence=0.98
        )
```

### RAG (Retrieval-Augmented Generation)

Implementei RAG completo para evitar alucinação de produtos:

1. **Ingestão**: Ao inicializar o banco, gera embeddings de cada tinta
2. **Vetorização**: Usa `text-embedding-3-small` da OpenAI
3. **Armazenamento**: Vector store com ChromaDB (local, sem dependências externas)
4. **Busca**: Busca por similaridade semântica + filtros estruturados

**Código**:

```python
class RAGService:
    def __init__(self, db: Session):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = Chroma(
            collection_name="paints_collection",
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
        )
    
    def search_paints(self, query: str, k: int = 5, filters: Dict = None):
        # Busca semântica
        results = self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filters  # Ex: {"ambiente": "Externo"}
        )
        return results
```

**Vantagens do RAG**:
- ✅ Elimina alucinação de produtos
- ✅ Busca por similaridade semântica (não precisa de keywords exatas)
- ✅ Combina busca vetorial + filtros estruturados
- ✅ Escalável (adicionar produtos não degrada performance)

### Memória Conversacional

Implementei dois níveis de memória:

#### 1. **Memória de Curto Prazo (Slot Memory)**

Slots que são preenchidos ao longo da conversa:

```python
class PaintContext(BaseModel):
    environment: Optional[str]      # interno ou externo
    surface_type: Optional[str]     # parede, madeira, metal
    color: Optional[str]            # cor mencionada
    finish_type: Optional[str]      # fosco, acetinado, brilhante
```

**Exemplo de uso**:
```
Turno 1: "Quero pintar meu quarto"
  → Slots: {environment: "interno", surface_type: "parede"}

Turno 2: "E fosco ou acetinado?"
  → Slots: {environment: "interno", surface_type: "parede", finish_type: "fosco"}
```

#### 2. **Memória de Longo Prazo (PostgreSQL)**

Todas as mensagens são persistidas no banco:

```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(20),  -- 'user' ou 'assistant'
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Isso permite:
- Histórico de conversas completo por usuário
- Analytics de uso do assistente
- Treinamento futuro (fine-tuning) com conversas reais

### Prompt Engineering

#### System Prompt Estruturado

```python
system_prompt = """
VOCÊ É UM CONSULTOR TÉCNICO ESPECIALISTA EM ACABAMENTOS E CORES.

REGRAS IMPORTANTES:
- Não mostre seu raciocínio passo a passo.
- Não repita cabeçalhos, JSON ou textos de sistema.
- Escreva como um humano: direto, consultivo, sem linguagem de debug.

DIRETRIZES DE ESTILO:
- Respostas naturais e humanas, sem parecer um robô de busca.
- Máximo de 4 frases curtas e impactantes.
- NUNCA use emojis.
- Sugira apenas 1 produto (o melhor para o caso).
- NÃO termine com perguntas. Só pergunte quando estritamente necessário.
"""
```

#### Prompt de Síntese Final (O Coração da Humanização)

```python
prompt = ChatPromptTemplate.from_template("""
    {style_guide}
    
    ---
    DADOS DO PRODUTO SELECIONADO:
    {paint_info}
    
    PARECER DOS ESPECIALISTAS TÉCNICOS:
    {specialist_insights}
    
    CONTEXTO ATUAL:
    Ambiente: {env} | Superfície: {surf} | Cor Focada: {color}
    ---
    
    MENSAGEM DO USUÁRIO: "{user_input}"
    
    TAREFA: Como um consultor, gere uma resposta que conecte o produto à necessidade do usuário. 
    REGRA CRÍTICA: Você só pode mencionar o produto em "DADOS DO PRODUTO SELECIONADO". Não invente.
    Não finalize com perguntas.
    Responda APENAS com o texto final ao usuário (sem cabeçalhos, sem JSON).
    
    RESPOSTA DO CONSULTOR:
""")
```

**Por que este prompt funciona**:
- ✅ Separa dados técnicos da síntese (evita dump de JSON)
- ✅ Restrição clara: só mencionar produto fornecido
- ✅ Tom consultivo e humanizado
- ✅ Guia de estilo integrado (máximo 4 frases, sem emojis)

### Geração de Visualizações com DALL-E

Quando o usuário pede para "mostrar", "visualizar" ou "ver como fica", o sistema:

1. Detecta a intenção via keywords
2. Extrai cor e ambiente do contexto
3. Gera prompt estruturado para DALL-E
4. Retorna URL da imagem gerada

**Código**:

```python
async def generate_paint_visualization(
    self, 
    color: str, 
    environment: str, 
    finish: str
) -> str:
    prompt = f"""
    Create a photorealistic interior design visualization of a {environment} 
    painted with {color} color paint with {finish} finish. 
    High quality, professional photography, natural lighting.
    """
    response = await self.client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return response.data[0].url
```

**Exemplo de resultado**:

```
Usuário: "Quero ver como fica meu escritório de cinza fosco"
IA: "Para o seu interior, recomendo a Suvinil Premium na cor Cinza Urbano."
    [Imagem gerada mostrando escritório pintado de cinza fosco]
```

---

## 🧰 Ferramentas de IA Utilizadas

### Durante o Desenvolvimento

#### 1. **Cursor AI**
**Uso**: IDE principal para desenvolvimento contextual com IA

**Exemplos de prompts utilizados**:
```

"Implemente extração de contexto conversacional usando LangChain, 
 identificando ambiente (interno/externo), superfície e cor desejada 
 a partir de mensagens do usuário."

"Evite que o LLM alucine produtos não cadastrados no banco, quero que ele só mencione tintas que existem no catálogo."
```

```
#### 3. **ChatGPT (OpenAI)**
**Uso**: revisão de código

"Revisar este Dockerfile e docker-compose.yml."
```

## 💡 O Que Faria Diferente

### Com Mais Tempo

#### 1. **Testes Automatizados** ⏳
Implementaria:
- Testes unitários para especialistas (pytest)
- Testes de RAG (validar recall e precisão)
- CI/CD com GitHub Actions

#### 2. **Streaming de Respostas** ⏳
Atualmente as respostas são síncronas. Implementaria:
- Server-Sent Events (SSE) para streaming
- Resposta chunk por chunk

#### 3. **Cache com Redis** ⏳
Para otimizar performance:
- Cache de embeddings gerados
- Cache de sessões de agentes (memória)
- Cache de consultas frequentes

#### 4. **Fine-tuning do Modelo** ⏳
Com conversas reais coletadas:
- Fine-tuning do GPT-4o-mini para tom Suvinil
- Redução de latência e custo
- Melhoria na humanização das respostas


## 📚 Recursos Adicionais

### Documentação

- **Backend API**: http://localhost:8000/docs (Swagger)
- **Frontend**: http://localhost:5173

### Endpoints Principais da API

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| POST | `/auth/register` | Registrar novo usuário | Não |
| POST | `/auth/login` | Login (retorna JWT) | Não |
| GET | `/users/me` | Dados do usuário atual | Sim |
| GET | `/paints` | Listar tintas (com filtros) | Sim |
| GET | `/paints/{id}` | Detalhes de uma tinta | Sim |
| POST | `/paints` | Criar tinta (admin) | Admin |
| PUT | `/paints/{id}` | Atualizar tinta (admin) | Admin |
| DELETE | `/paints/{id}` | Deletar tinta (admin) | Admin |
| POST | `/ai/chat` | Enviar mensagem para o assistente | Sim |
| POST | `/ai/chat/reset` | Resetar conversa | Sim |
| GET | `/ai/chat/history` | Obter histórico de mensagens | Sim |
| DELETE | `/ai/chat/history` | Limpar histórico | Sim |
| GET | `/ai/status` | Status do serviço de IA | Não |

---

## 🎓 Conclusão

Este projeto demonstra a aplicação prática de conceitos modernos de IA em um caso de uso real: **recomendação inteligente de produtos**. Combina:

- **Engenharia de Software**: Clean Architecture, SOLID, Docker
- **Inteligência Artificial**: LangChain, RAG, Multi-Agentes, Prompt Engineering
- **Experiência do Usuário**: Frontend moderno, respostas humanizadas, visualizações

O sistema é **escalável**, **manutenível** e **extensível**, pronto para ser evoluído em um contexto de produção.

---

## 👨‍💻 Autor

**Luana Salmito**  
Desenvolvido para o **Desafio Backend IA - Loomi**  
Janeiro 2026

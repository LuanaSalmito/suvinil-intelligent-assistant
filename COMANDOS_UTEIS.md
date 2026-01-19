# 🚀 Comandos Úteis - Sistema Suvinil IA

## 📦 Setup Inicial

```bash
# Navegar para o diretório do backend
cd suvinil-ai

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências (se necessário)
pip install -r requirements.txt
```

---

## 🎨 Popular Banco de Dados com Tintas

```bash
# 1. Gerar CSV com 100 tintas mockadas
python scripts/generate_mock_paints.py

# 2. Importar tintas para o banco (limpa banco antes)
python scripts/import_paints_to_db.py

# 3. (Opcional) Reindexar RAG
python scripts/reindex_rag.py

# 4. Testar se funcionou
python scripts/test_color_filtering.py
```

---

## 🧪 Testes

```bash
# Teste completo do sistema de cores
python scripts/test_chat_integration.py

# Teste de filtro de cores
python scripts/test_color_filtering.py

# Verificar tintas no banco
python scripts/test_color_filtering.py | grep -A 5 "Total de tintas"
```

---

## 🗄️ Banco de Dados

```bash
# Listar cores disponíveis
python -c "
from app.core.database import SessionLocal
from app.repositories.paint_repository import PaintRepository
db = SessionLocal()
colors = PaintRepository.get_available_colors(db)
for c in colors:
    print(f'{c[\"color_display\"]}: {c[\"count\"]} tintas')
db.close()
"

# Contar total de tintas
python -c "
from app.core.database import SessionLocal
from app.repositories.paint_repository import PaintRepository
db = SessionLocal()
paints = PaintRepository.get_all(db, limit=1000)
print(f'Total: {len(paints)} tintas')
db.close()
"

# Buscar tintas azuis
python -c "
from app.core.database import SessionLocal
from app.repositories.paint_repository import PaintRepository
db = SessionLocal()
paints = PaintRepository.find_by_color(db, 'azul', limit=5)
for p in paints:
    print(f'{p.name} - R\$ {p.price:.2f}')
db.close()
"
```

---

## 🚀 Rodar Aplicação

```bash
# Backend (API)
cd suvinil-ai
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (em outro terminal)
cd suvinil-frontend
npm run dev
```

---

## 🔧 Migrações do Banco

```bash
cd suvinil-ai
source venv/bin/activate

# Criar nova migração
alembic revision --autogenerate -m "descrição da mudança"

# Aplicar migrações
alembic upgrade head

# Reverter última migração
alembic downgrade -1

# Ver histórico de migrações
alembic history
```

---

## 📝 Logs e Debug

```bash
# Ver logs do backend em tempo real
cd suvinil-ai
source venv/bin/activate
uvicorn main:app --reload --log-level debug

# Testar endpoint de chat diretamente
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{"message": "quero tinta azul"}'

# Verificar status da IA
curl http://localhost:8000/api/v1/ai/status
```

---

## 🧹 Limpeza

```bash
# Limpar todas as tintas do banco
python -c "
from app.core.database import SessionLocal
from app.models.paint import Paint
db = SessionLocal()
db.query(Paint).delete()
db.commit()
print('✓ Banco limpo')
db.close()
"

# Limpar cache do Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Limpar vector store do RAG
rm -rf suvinil-ai/chroma_db
```

---

## 📊 Estatísticas

```bash
# Estatísticas do catálogo
python scripts/test_color_filtering.py | grep -E "Total|Azul|Verde|Vermelho"

# Ver todas as cores disponíveis
python -c "
from app.core.database import SessionLocal
from app.repositories.paint_repository import PaintRepository
db = SessionLocal()
colors = PaintRepository.get_available_colors(db)
print(f'Cores disponíveis: {len(colors)}')
for c in colors[:10]:
    print(f'  {c[\"color_display\"]}: {c[\"count\"]} tintas')
db.close()
"
```

---

## 🔐 Usuários e Autenticação

```bash
# Criar usuário admin (via Python)
python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
db = SessionLocal()
user = User(
    email='admin@suvinil.com',
    hashed_password=get_password_hash('admin123'),
    full_name='Admin',
    is_admin=True,
    is_active=True
)
db.add(user)
db.commit()
print('✓ Usuário admin criado')
db.close()
"
```

---

## 📦 Docker (Produção)

```bash
# Build e rodar containers
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar containers
docker-compose down

# Rebuild após mudanças
docker-compose up -d --build

# Executar comando no container
docker-compose exec backend python scripts/import_paints_to_db.py
```

---

## 🎯 Atalhos Úteis

```bash
# Alias úteis (adicione ao ~/.bashrc ou ~/.zshrc)
alias suvinil-backend='cd ~/luana/suvinil-intelligent-assistant/suvinil-ai && source venv/bin/activate'
alias suvinil-frontend='cd ~/luana/suvinil-intelligent-assistant/suvinil-frontend'
alias suvinil-test='cd ~/luana/suvinil-intelligent-assistant/suvinil-ai && source venv/bin/activate && python scripts/test_chat_integration.py'
alias suvinil-populate='cd ~/luana/suvinil-intelligent-assistant/suvinil-ai && source venv/bin/activate && python scripts/generate_mock_paints.py && python scripts/import_paints_to_db.py'
```

---

## 🔍 Troubleshooting

```bash
# Verificar se backend está rodando
curl http://localhost:8000/docs

# Verificar conexão com banco
python -c "
from app.core.database import engine
try:
    engine.connect()
    print('✓ Conexão com banco OK')
except Exception as e:
    print(f'✗ Erro: {e}')
"

# Verificar instalação do Python
python --version
pip list | grep -E "fastapi|sqlalchemy|langchain|openai"

# Verificar variáveis de ambiente
cd suvinil-ai
cat .env | grep -v "^#" | grep -v "^$"
```

---

## 📚 Documentação da API

```bash
# Abrir documentação Swagger no navegador
# (com backend rodando)
open http://localhost:8000/docs

# Ou ReDoc
open http://localhost:8000/redoc
```

---

## 🎨 Comandos Rápidos (One-liners)

```bash
# Setup completo do zero
cd ~/luana/suvinil-intelligent-assistant/suvinil-ai && \
  source venv/bin/activate && \
  python scripts/generate_mock_paints.py && \
  python scripts/import_paints_to_db.py && \
  python scripts/test_chat_integration.py

# Ver cores com mais tintas
python -c "from app.core.database import SessionLocal; from app.repositories.paint_repository import PaintRepository; db = SessionLocal(); colors = PaintRepository.get_available_colors(db); [print(f'{c[\"color_display\"]}: {c[\"count\"]}') for c in colors]; db.close()"

# Buscar tinta específica por ID
python -c "from app.core.database import SessionLocal; from app.repositories.paint_repository import PaintRepository; db = SessionLocal(); p = PaintRepository.get_by_id(db, 1); print(f'{p.name} - {p.color_name} - R\$ {p.price:.2f}') if p else print('Não encontrado'); db.close()"
```

---

## 💡 Dicas

- Use `source venv/bin/activate` SEMPRE antes de rodar scripts Python
- Mantenha o `.env` atualizado com credenciais corretas
- Execute `test_chat_integration.py` após mudanças importantes
- Reimporte tintas após modificar `generate_mock_paints.py`
- O sistema funciona perfeitamente sem OpenAI (modo fallback)

---

Última atualização: 2026-01-18

# Scripts de Gerenciamento de Tintas

Este diretório contém scripts úteis para popular e gerenciar o banco de dados de tintas.

## Scripts Disponíveis

### 1. `generate_mock_paints.py`
Gera um arquivo CSV com 100 tintas mockadas com dados variados.

**Uso:**
```bash
python scripts/generate_mock_paints.py
```

**Saída:**
- Arquivo `paints_mock_100.csv` com 100 tintas

**Distribuição de cores:**
- Azul: ~15 tintas
- Vermelho: ~15 tintas
- Verde: ~10 tintas
- Branco: ~11 tintas
- Outras cores: ~49 tintas

---

### 2. `import_paints_to_db.py`
Importa tintas do CSV para o banco de dados PostgreSQL.

**Uso:**
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Importar tintas (limpa banco antes)
python scripts/import_paints_to_db.py
```

**Funcionalidades:**
- ✅ Limpa banco antes de importar (opcional)
- ✅ Importa todas as tintas do CSV
- ✅ Valida enums (Environment, FinishType, PaintLine)
- ✅ Mostra relatório detalhado
- ✅ Verifica importação com estatísticas por cor

---

### 3. `reindex_rag.py`
Reindexa o vector store do RAG após adicionar/modificar tintas.

**Uso:**
```bash
source venv/bin/activate
python scripts/reindex_rag.py
```

**Nota:** Requer API key válida da OpenAI. Se não estiver disponível, o sistema usa modo fallback automático.

---

### 4. `test_color_filtering.py`
Testa se o filtro de cores está funcionando corretamente.

**Uso:**
```bash
source venv/bin/activate
python scripts/test_color_filtering.py
```

**Verifica:**
- ✅ Total de tintas no banco
- ✅ Filtro por cor específica (azul, verde, etc.)
- ✅ Filtro combinado (cor + ambiente)
- ✅ Estatísticas por cor

---

## Workflow Completo

Para popular o banco do zero:

```bash
# 1. Gerar CSV com tintas mockadas
python scripts/generate_mock_paints.py

# 2. Ativar ambiente virtual
source venv/bin/activate

# 3. Importar para banco de dados
python scripts/import_paints_to_db.py

# 4. (Opcional) Reindexar RAG
python scripts/reindex_rag.py

# 5. Testar filtros
python scripts/test_color_filtering.py
```

---

## Estrutura do CSV

Colunas:
- `id`: ID único da tinta
- `name`: Nome da tinta
- `color`: Código/hex da cor
- `color_name`: Nome da cor (Azul, Verde, etc.)
- `surface_type`: Tipo de superfície (parede, madeira, azulejo, metal)
- `environment`: Ambiente (interno, externo, ambos)
- `finish_type`: Acabamento (fosco, acetinado, brilhante, semi-brilhante)
- `features`: Características (lavável, sem odor, etc.)
- `line`: Linha do produto (Premium, Standard, Economy)
- `price`: Preço em R$
- `description`: Descrição da tinta
- `is_active`: Status (true/false)

---

## Dados Atuais

Após executar os scripts, o banco terá:

- **100 tintas** no total
- **15 tintas azuis** (8 para ambiente interno)
- **15 tintas vermelhas**
- **11 tintas brancas**
- **10 tintas verdes**
- **10 tintas laranja**
- **9 tintas rosas**
- **9 tintas marrons**
- **8 tintas cinza**
- **7 tintas amarelas**
- **6 tintas pretas**

---

## Troubleshooting

### Erro: ModuleNotFoundError
**Solução:** Ative o ambiente virtual antes de executar:
```bash
source venv/bin/activate
```

### Erro: Database connection failed
**Solução:** Verifique se o PostgreSQL está rodando e as variáveis de ambiente no `.env` estão corretas.

### Erro: OpenAI quota exceeded (RAG)
**Solução:** Não é problema! O sistema funciona perfeitamente no modo fallback sem a OpenAI. O filtro de cores funciona independentemente do RAG.

---

## Notas Importantes

1. O script `import_paints_to_db.py` **limpa o banco** antes de importar por padrão
2. As tintas são geradas aleatoriamente a cada execução do `generate_mock_paints.py`
3. O sistema de IA funciona em modo fallback se a OpenAI não estiver disponível
4. Os filtros de cor funcionam corretamente no modo fallback

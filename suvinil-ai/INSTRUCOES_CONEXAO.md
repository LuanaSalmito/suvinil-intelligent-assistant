# Instruções para Conectar e Iniciar o Backend

## 1. Configurar Senha do PostgreSQL (Recomendado)

Se você ainda não tem senha configurada para o usuário `postgres`, configure agora:

```bash
sudo -u postgres psql
```

Dentro do psql, execute:
```sql
ALTER USER postgres PASSWORD 'sua_senha_aqui';
\q
```

Depois, atualize o arquivo `.env`:
```
DATABASE_URL=postgresql://postgres:sua_senha_aqui@localhost:5432/suvinil_db
```

## 2. Ativar Ambiente Virtual (se existir)

```bash
cd /home/jacques/luana/suvinil-intelligent-assistant/suvinil-ai

# Se já existe venv:
source venv/bin/activate

# Ou criar novo venv:
python3 -m venv venv
source venv/bin/activate
```

## 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

## 4. Inicializar o Banco de Dados

```bash
python -m app.core.init_db
```

Isso irá:
- Criar todas as tabelas necessárias
- Criar usuários de exemplo (admin/admin123, user/user123)
- Adicionar tintas de exemplo

## 5. Iniciar o Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 6. Testar a API

Abra no navegador:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## ⚠️ Solução de Problemas

### Erro: "Peer authentication failed"
Se der erro de autenticação, você tem 2 opções:

**Opção A:** Configurar senha (recomendado)
```bash
sudo -u postgres psql
ALTER USER postgres PASSWORD 'sua_senha';
\q
```

**Opção B:** Criar um usuário específico para a aplicação
```bash
sudo -u postgres psql
CREATE USER suvinil_user WITH PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE suvinil_db TO suvinil_user;
\q
```

Depois atualize o `.env`:
```
DATABASE_URL=postgresql://suvinil_user:senha_segura@localhost:5432/suvinil_db
```

### Erro: "ModuleNotFoundError"
Certifique-se de que o ambiente virtual está ativado e as dependências instaladas.

### Verificar se o PostgreSQL está rodando
```bash
sudo systemctl status postgresql
# Ou iniciar:
sudo systemctl start postgresql
```

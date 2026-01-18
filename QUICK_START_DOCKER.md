# 🚀 Quick Start - Docker

## Iniciar Tudo com Um Comando

```bash
# Na raiz do projeto
docker-compose up -d
```

Ou use o script:

```bash
./start-docker.sh
```

Ou use o Makefile:

```bash
make up
```

## ✅ O Que Vai Acontecer

1. **PostgreSQL** inicia (porta 5432)
2. **Backend** aguarda PostgreSQL → Roda migrações → Inicializa dados → Inicia API (porta 8000)
3. **Frontend** aguarda backend → Inicia servidor Vite (porta 5173)

## 🌐 Acessar

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

## 📋 Comandos Úteis

```bash
# Ver logs
docker-compose logs -f

# Parar tudo
docker-compose down

# Rebuild após mudanças
docker-compose up -d --build

# Ver status
docker-compose ps
```

## 🔧 Configuração

Crie um arquivo `.env` na raiz (opcional):

```env
SECRET_KEY=sua-chave-secreta-aqui
OPENAI_API_KEY=sua-chave-openai
VITE_API_URL=http://localhost:8000
```

## 🐛 Problemas?

### Portas já em uso
```bash
# Ver o que está usando a porta
lsof -i :8000
lsof -i :5173
lsof -i :5432

# Parar processos ou mudar portas no docker-compose.yml
```

### Ver logs de erro
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

### Limpar e recomeçar
```bash
docker-compose down -v
docker-compose up -d --build
```

## 📚 Mais Informações

Veja `README_DOCKER.md` para documentação completa.

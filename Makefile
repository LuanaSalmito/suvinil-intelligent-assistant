.PHONY: up down build restart logs clean help

# Comandos principais
up:
	@echo "🚀 Iniciando aplicação..."
	docker-compose up -d
	@echo "✅ Aplicação iniciada!"
	@echo "📍 Frontend: http://localhost:5173"
	@echo "📍 Backend:  http://localhost:8000"
	@echo "📍 Swagger:  http://localhost:8000/docs"
	@echo "🌐 Abrindo Frontend e Swagger no navegador..."
	@sh -c 'OPEN=""; for c in xdg-open wslview open; do command -v $$c >/dev/null 2>&1 && OPEN=$$c && break; done; \
		if [ -n "$$OPEN" ]; then \
			($$OPEN http://localhost:5173 >/dev/null 2>&1 &); \
			($$OPEN http://localhost:8000/docs >/dev/null 2>&1 &); \
		else \
			echo "⚠️ Não encontrei comando para abrir navegador (xdg-open/wslview/open)."; \
			echo "Abra manualmente: http://localhost:5173 e http://localhost:8000/docs"; \
		fi' || true

down:
	@echo "🛑 Parando aplicação..."
	docker-compose down

build:
	@echo "🔨 Fazendo build das imagens..."
	docker-compose build

restart:
	@echo "🔄 Reiniciando aplicação..."
	docker-compose restart

logs:
	@echo "📋 Logs da aplicação..."
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-db:
	docker-compose logs -f postgres

# Comandos de desenvolvimento
shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend sh

# Comandos de banco
db-migrate:
	@echo "🔄 Rodando migrações..."
	docker-compose exec backend alembic upgrade head

db-init:
	@echo "📊 Inicializando banco de dados..."
	docker-compose exec backend python -m app.core.init_db

db-shell:
	docker-compose exec postgres psql -U postgres -d suvinil_db

# Limpeza
clean:
	@echo "🧹 Limpando containers e volumes..."
	docker-compose down -v

clean-all:
	@echo "🧹 Limpando tudo (containers, volumes, imagens)..."
	docker-compose down -v --rmi all

# Produção
prod-up:
	@echo "🏭 Iniciando aplicação em modo produção..."
	docker-compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Help
help:
	@echo "🐳 Comandos Docker disponíveis:"
	@echo ""
	@echo "  make up              - Inicia aplicação"
	@echo "  make down            - Para aplicação"
	@echo "  make build           - Faz build das imagens"
	@echo "  make restart         - Reinicia aplicação"
	@echo "  make logs            - Ver logs de todos os serviços"
	@echo "  make logs-backend    - Ver logs do backend"
	@echo "  make logs-frontend   - Ver logs do frontend"
	@echo ""
	@echo "  make shell-backend   - Abrir shell no backend"
	@echo "  make shell-frontend  - Abrir shell no frontend"
	@echo ""
	@echo "  make db-migrate      - Rodar migrações do banco"
	@echo "  make db-init         - Inicializar banco de dados"
	@echo "  make db-shell        - Abrir shell do PostgreSQL"
	@echo ""
	@echo "  make clean           - Limpar containers e volumes"
	@echo "  make clean-all       - Limpar tudo (incluindo imagens)"
	@echo ""
	@echo "  make prod-up         - Iniciar em modo produção"
	@echo "  make prod-down       - Parar aplicação em produção"

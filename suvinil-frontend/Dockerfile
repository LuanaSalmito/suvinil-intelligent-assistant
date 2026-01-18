# Dockerfile para Frontend (React/Vite)
FROM node:18-alpine

WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências
RUN npm ci

# Copiar código da aplicação
COPY . .

# Expor porta do Vite
EXPOSE 5173

# Comando para desenvolvimento (hot reload)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

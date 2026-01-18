# Solução: Erro 401 (Unauthorized) no Frontend

## Problema

O frontend está recebendo erro `401 Unauthorized` em algumas requisições.

## Causas Possíveis

1. **Token expirado ou inválido**
2. **Tentando acessar endpoint protegido sem token**
3. **Token não está sendo enviado corretamente**
4. **Backend rejeitando token**

## Soluções Implementadas

### 1. Interceptor Melhorado

O interceptor agora:
- ✅ Só limpa token se havia um token (usuário estava autenticado)
- ✅ Não redireciona automaticamente para endpoints que funcionam sem auth
- ✅ Permite que componentes tratem erros 401 quando apropriado

### 2. Verificações

#### Verificar se o token existe:
```javascript
// No console do navegador
localStorage.getItem('token')
```

#### Verificar se o token é válido:
```javascript
// No console do navegador
const token = localStorage.getItem('token');
if (token) {
  // Decodificar token (apenas para debug)
  const payload = JSON.parse(atob(token.split('.')[1]));
  console.log('Token expira em:', new Date(payload.exp * 1000));
  console.log('Token atual:', new Date());
}
```

## Como Debugar

### 1. Abrir DevTools (F12)
- Vá para a aba **Network**
- Procure pela requisição que está dando 401
- Veja os **Headers** da requisição

### 2. Verificar Headers Enviados

A requisição deve ter:
```
Authorization: Bearer <seu_token>
```

Se não tiver, o token não está sendo enviado.

### 3. Verificar Resposta do Backend

Na aba **Network**, clique na requisição com erro 401 e veja:
- **Response**: O que o backend retornou
- **Request Headers**: Se o token foi enviado

## Soluções Rápidas

### Solução 1: Fazer Login Novamente

Se o token expirou:
1. Vá para `/login`
2. Faça login novamente
3. O token será atualizado

### Solução 2: Limpar Storage e Tentar Novamente

```javascript
// No console do navegador
localStorage.clear();
// Recarregue a página
location.reload();
```

### Solução 3: Verificar se Backend está Rodando

```bash
curl http://localhost:8000/health
```

Se não responder, o backend não está rodando.

### Solução 4: Verificar CORS

Se o erro for de CORS, verifique se o backend permite a origem do frontend:

```python
# No backend (main.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Endpoints que Funcionam SEM Autenticação

- ✅ `GET /paints` - Listar tintas
- ✅ `GET /paints/{id}` - Ver tinta específica
- ✅ `POST /ai/chat` - Chat (funciona sem auth)
- ✅ `POST /auth/login` - Login
- ✅ `POST /auth/register` - Registro

## Endpoints que REQUEREM Autenticação

- ❌ `GET /users/me` - Perfil do usuário
- ❌ `POST /paints` - Criar tinta (requer ADMIN)
- ❌ `PUT /paints/{id}` - Atualizar tinta (requer ADMIN)
- ❌ `DELETE /paints/{id}` - Deletar tinta (requer ADMIN)
- ❌ `POST /users/` - Criar usuário (requer ADMIN)

## Teste Rápido

Execute no console do navegador:

```javascript
// Testar se API está acessível
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);

// Testar se token existe
console.log('Token:', localStorage.getItem('token'));

// Testar endpoint público
fetch('http://localhost:8000/paints')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

## Se o Problema Persistir

1. Verifique os logs do backend
2. Verifique se o token está sendo gerado corretamente no login
3. Verifique se o backend está validando o token corretamente
4. Verifique se há problemas de CORS

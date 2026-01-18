# Debug: Erro 401 Unauthorized

## Passos para Identificar o Problema

### 1. Abrir Console do Navegador (F12)

### 2. Verificar Token

```javascript
// Cole no console
console.log('Token:', localStorage.getItem('token'));
console.log('User:', localStorage.getItem('user'));
```

### 3. Verificar Requisição que Falhou

1. Abra a aba **Network** no DevTools
2. Procure pela requisição com status 401
3. Clique nela e veja:
   - **Request Headers**: Tem `Authorization: Bearer ...`?
   - **Response**: O que o backend retornou?

### 4. Testar Endpoint Manualmente

```javascript
// Teste endpoint público (não deve dar 401)
fetch('http://localhost:8000/paints')
  .then(r => r.json())
  .then(d => console.log('✅ Paints OK:', d))
  .catch(e => console.error('❌ Erro:', e));

// Teste endpoint protegido (pode dar 401 se não tiver token)
const token = localStorage.getItem('token');
fetch('http://localhost:8000/users/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
  .then(r => {
    if (r.status === 401) {
      console.error('❌ Token inválido ou expirado');
      return r.json();
    }
    return r.json();
  })
  .then(d => console.log('✅ User OK:', d))
  .catch(e => console.error('❌ Erro:', e));
```

## Problemas Comuns e Soluções

### Problema 1: Token não está sendo enviado

**Sintoma**: Request Headers não tem `Authorization`

**Solução**: 
- Verificar se `localStorage.getItem('token')` retorna algo
- Verificar se o interceptor está funcionando

### Problema 2: Token expirado

**Sintoma**: Token existe mas backend retorna 401

**Solução**: Fazer login novamente

### Problema 3: Backend não está rodando

**Sintoma**: Erro de conexão (não é 401, é erro de rede)

**Solução**: Verificar se backend está rodando em http://localhost:8000

### Problema 4: CORS

**Sintoma**: Erro de CORS no console

**Solução**: Verificar configuração CORS no backend

## Limpar Tudo e Começar de Novo

```javascript
// Cole no console para limpar tudo
localStorage.clear();
sessionStorage.clear();
location.reload();
```

## Verificar se Backend Está Funcionando

```bash
# No terminal
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

Se não responder, o backend não está rodando.

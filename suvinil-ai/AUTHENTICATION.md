# Sistema de Autenticação e RBAC

## Visão Geral

O sistema implementa autenticação JWT com Role-Based Access Control (RBAC) seguindo boas práticas de Clean Architecture e SOLID.

## Estrutura de Autenticação

### 1. JWT (JSON Web Tokens)

- **Algoritmo**: HS256
- **Expiração**: Configurável via `ACCESS_TOKEN_EXPIRE_MINUTES` (padrão: 30 minutos)
- **Secret Key**: Configurada via `SECRET_KEY` no arquivo `.env`

### 2. Roles (Papéis)

O sistema possui dois níveis de acesso:

- **`ADMIN`**: Acesso completo
  - ✅ Usar o chatbot
  - ✅ Gerenciar catálogo (criar, editar, deletar tintas)
  - ✅ Gerenciar usuários
  
- **`USER`**: Acesso básico
  - ✅ Usar o chatbot
  - ❌ Gerenciar catálogo (apenas visualizar)
  - ❌ Gerenciar usuários

### 3. Endpoints de Autenticação

#### POST `/auth/login`

Autentica um usuário e retorna um JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Uso do Token:**
```
Authorization: Bearer <token>
```

## Proteção de Rotas

### Dependencies Disponíveis

1. **`get_current_user`**: Obtém usuário do token (obrigatório)
2. **`get_current_active_user`**: Obtém usuário ativo (opcional)
3. **`require_authenticated_user`**: Requer usuário autenticado e ativo
4. **`require_role([UserRole.ADMIN])`**: Requer role específica

### Exemplos de Uso

#### Endpoint Público (sem autenticação)
```python
@router.get("/paints")
async def list_paints(db: Session = Depends(get_db)):
    # Qualquer um pode acessar
    pass
```

#### Endpoint com Autenticação Opcional
```python
@router.post("/ai/chat")
async def chat(
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    # Funciona com ou sem autenticação
    if current_user:
        # Usuário autenticado
        pass
    else:
        # Usuário anônimo
        pass
```

#### Endpoint que Requer Autenticação
```python
@router.get("/users/me")
async def get_me(
    current_user: dict = Depends(require_authenticated_user),
):
    # Requer autenticação
    return current_user
```

#### Endpoint que Requer Role Específica
```python
@router.post("/paints")
async def create_paint(
    paint_data: PaintCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    # Apenas ADMIN pode criar tintas
    pass
```

## Fluxo de Autenticação

### 1. Login

```
1. Usuário envia username e password
2. Sistema verifica credenciais
3. Sistema verifica se usuário está ativo
4. Sistema gera JWT token com:
   - sub: username
   - user_id: id do usuário
   - role: role do usuário (admin/user)
   - email: email do usuário
   - exp: data de expiração
5. Token é retornado ao cliente
```

### 2. Uso do Token

```
1. Cliente armazena token (localStorage no frontend)
2. Cliente envia token no header: Authorization: Bearer <token>
3. Backend valida token:
   - Verifica assinatura
   - Verifica expiração
   - Busca usuário no banco
   - Verifica se usuário está ativo
4. Backend retorna dados do usuário
```

### 3. Verificação de Permissões

```
1. Dependency verifica se usuário está autenticado
2. Dependency verifica role do usuário
3. Se role não permitir acesso, retorna 403 Forbidden
4. Se tudo OK, permite acesso ao endpoint
```

## Endpoints Protegidos

### Chat (`/ai/chat`)
- **Acesso**: Público (funciona sem autenticação)
- **Com autenticação**: Sessão persistente por usuário
- **Sem autenticação**: Sessão temporária anônima

### Catálogo de Tintas (`/paints`)

#### GET `/paints`
- **Acesso**: Público
- **Descrição**: Lista tintas (qualquer um pode ver)

#### POST `/paints`
- **Acesso**: Apenas ADMIN
- **Descrição**: Cria nova tinta

#### PUT `/paints/{id}`
- **Acesso**: Apenas ADMIN
- **Descrição**: Atualiza tinta existente

#### DELETE `/paints/{id}`
- **Acesso**: Apenas ADMIN
- **Descrição**: Deleta tinta

## Segurança

### Boas Práticas Implementadas

1. ✅ **Senhas hasheadas**: Usando bcrypt
2. ✅ **JWT com expiração**: Tokens expiram automaticamente
3. ✅ **Validação de usuário ativo**: Usuários inativos não podem fazer login
4. ✅ **RBAC**: Controle de acesso baseado em roles
5. ✅ **Validação de token**: Token é validado em cada requisição
6. ✅ **Mensagens de erro genéricas**: Não expõe informações sensíveis

### Recomendações para Produção

1. **Secret Key**: Use uma chave forte e única (mínimo 32 caracteres)
2. **HTTPS**: Sempre use HTTPS em produção
3. **Rate Limiting**: Implemente rate limiting no login
4. **Refresh Tokens**: Considere implementar refresh tokens
5. **Logging**: Implemente logging de tentativas de login
6. **2FA**: Considere autenticação de dois fatores para admins

## Credenciais de Teste

### Admin
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `ADMIN`
- **Permissões**: Chat + Gerenciar Catálogo

### User
- **Username**: `user`
- **Password**: `user123`
- **Role**: `USER`
- **Permissões**: Chat apenas

## Exemplo de Uso no Frontend

```javascript
// Login
const response = await authApi.login(username, password);
localStorage.setItem('token', response.access_token);

// Requisições autenticadas
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});

// Verificar se é admin
const user = authApi.getCurrentUser();
if (user?.role === 'admin') {
  // Mostrar opções de admin
}
```

## Troubleshooting

### Token Expirado
- **Erro**: `401 Unauthorized`
- **Solução**: Fazer login novamente

### Permissão Insuficiente
- **Erro**: `403 Forbidden`
- **Solução**: Verificar se usuário tem role adequada

### Usuário Inativo
- **Erro**: `400 Bad Request - Inactive user`
- **Solução**: Ativar usuário no banco de dados

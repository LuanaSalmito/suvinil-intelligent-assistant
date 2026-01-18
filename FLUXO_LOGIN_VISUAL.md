# 🔐 Fluxo Visual de Autenticação - Backend ↔ Frontend

## 📊 Diagrama de Sequência

```
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│   Frontend   │              │   Backend    │              │   Database   │
│   (React)    │              │  (FastAPI)   │              │ (PostgreSQL) │
└──────┬───────┘              └──────┬───────┘              └──────┬───────┘
       │                              │                              │
       │  1. POST /auth/login         │                              │
       │  {username, password}        │                              │
       ├─────────────────────────────>│                              │
       │                              │                              │
       │                              │  2. Buscar User              │
       │                              │  WHERE username = ?          │
       │                              ├──────────────────────────────>│
       │                              │                              │
       │                              │  3. Retorna User             │
       │                              │<──────────────────────────────┤
       │                              │                              │
       │                              │  4. verify_password()        │
       │                              │  Compara senha com hash       │
       │                              │                              │
       │                              │  5. create_access_token()    │
       │                              │  Gera JWT com user data      │
       │                              │                              │
       │  6. Retorna Token            │                              │
       │  {access_token, token_type}  │                              │
       │<─────────────────────────────┤                              │
       │                              │                              │
       │  7. Salva token              │                              │
       │  localStorage.setItem()      │                              │
       │                              │                              │
       │                              │                              │
       │  8. GET /users/me            │                              │
       │  Authorization: Bearer token  │                              │
       ├─────────────────────────────>│                              │
       │                              │                              │
       │                              │  9. decode_access_token()    │
       │                              │  Valida e decodifica JWT      │
       │                              │                              │
       │                              │  10. Buscar User completo    │
       │                              ├──────────────────────────────>│
       │                              │                              │
       │                              │  11. Retorna User            │
       │                              │<──────────────────────────────┤
       │                              │                              │
       │  12. Retorna User Data       │                              │
       │  {id, username, role, ...}   │                              │
       │<─────────────────────────────┤                              │
       │                              │                              │
       │  13. Salva User              │                              │
       │  localStorage.setItem()      │                              │
       │                              │                              │
       │  14. Atualiza Estado         │                              │
       │  setUser(), setIsAuth(true)   │                              │
       │                              │                              │
       │  15. Redireciona para /chat  │                              │
       │                              │                              │
```

## 🔑 Componentes Principais

### 1. Modelo User (Backend)

```python
# suvinil-ai/app/models/user.py
class User(Base):
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)      # "admin"
    email = Column(String, unique=True)          # "admin@suvinil.com"
    hashed_password = Column(String)             # "$2b$12$LQv3c1yq..." (bcrypt)
    role = Column(Enum(UserRole))                # ADMIN ou USER
    is_active = Column(Boolean, default=True)     # True/False
```

**Por que `hashed_password`?**
- ❌ **NUNCA** armazene senha em texto plano
- ✅ Use hash bcrypt (irreversível)
- ✅ Compara hash ao fazer login

### 2. Segurança (Backend)

```python
# suvinil-ai/app/core/security.py

# Ao criar usuário
hashed = get_password_hash("senha123")
# Resultado: "$2b$12$LQv3c1yqBWVHxkd0LHAkCO..."

# Ao fazer login
verify_password("senha123", hashed)  # True ou False
```

### 3. JWT Token

```python
# Criar token
token = create_access_token({
    "sub": "admin",           # Subject (username)
    "user_id": 1,             # ID do usuário
    "role": "admin",          # Role (admin/user)
    "email": "admin@...",     # Email
    "exp": 1234567890         # Expiração (timestamp)
})

# Token gerado (exemplo):
# "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVzZXJfaWQiOjEsInJvbGUiOiJhZG1pbiIsImV4cCI6MTIzNDU2Nzg5MH0.signature"
```

**Estrutura do Token:**
```
eyJhbGci...  ← Header (algoritmo)
.eyJzdWIi... ← Payload (dados do usuário)
.signature   ← Assinatura (validação)
```

### 4. Endpoint de Login (Backend)

```python
# suvinil-ai/app/api/v1/auth.py

@router.post("/login")
async def login(credentials: UserLogin, db: Session):
    # 1. Buscar usuário
    user = UserRepository.get_by_username(db, credentials.username)
    
    # 2. Verificar senha
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(401, "Incorrect password")
    
    # 3. Gerar token
    token = create_access_token({
        "sub": user.username,
        "user_id": user.id,
        "role": user.role.value
    })
    
    # 4. Retornar
    return {"access_token": token, "token_type": "bearer"}
```

### 5. Frontend - API Client

```javascript
// suvinil-frontend/src/lib/api.js

// Configuração
const api = axios.create({
  baseURL: 'http://localhost:8000'
});

// Interceptor: Adiciona token automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Função de login
export const authApi = {
  login: async (username, password) => {
    // 1. Envia credenciais
    const response = await api.post('/auth/login', { username, password });
    
    // 2. Salva token
    localStorage.setItem('token', response.data.access_token);
    
    // 3. Busca informações do usuário
    const userResponse = await api.get('/users/me');
    localStorage.setItem('user', JSON.stringify(userResponse.data));
    
    return userResponse.data;
  }
};
```

### 6. Frontend - Context

```javascript
// suvinil-frontend/src/contexts/AuthContext.jsx

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = async (username, password) => {
    const userData = await authApi.login(username, password);
    setUser(userData);
    setIsAuthenticated(true);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### 7. Frontend - Página de Login

```javascript
// suvinil-frontend/src/pages/Login.jsx

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    await login(username, password);
    navigate('/chat');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={username} onChange={(e) => setUsername(e.target.value)} />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Entrar</button>
    </form>
  );
}
```

## 🔄 Fluxo Completo Detalhado

### Passo 1: Usuário Preenche Formulário
```
Frontend (Login.jsx)
├─ Usuário digita: username="admin"
├─ Usuário digita: password="admin123"
└─ Clica em "Entrar"
```

### Passo 2: Frontend Chama API
```javascript
// Login.jsx
await login("admin", "admin123")

// AuthContext.jsx
await authApi.login("admin", "admin123")

// api.js
POST http://localhost:8000/auth/login
Body: { "username": "admin", "password": "admin123" }
```

### Passo 3: Backend Processa
```python
# auth.py recebe
credentials = { username: "admin", password: "admin123" }

# Busca no banco
user = db.query(User).filter(User.username == "admin").first()
# Retorna: User(id=1, username="admin", hashed_password="$2b$12$...", role="admin")

# Verifica senha
verify_password("admin123", user.hashed_password)
# Compara "admin123" com "$2b$12$LQv3c1yq..." → True

# Gera token
token = jwt.encode({
    "sub": "admin",
    "user_id": 1,
    "role": "admin",
    "exp": 1234567890
}, SECRET_KEY)
# Resultado: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Retorna
return { "access_token": "eyJhbGci...", "token_type": "bearer" }
```

### Passo 4: Frontend Recebe Token
```javascript
// api.js recebe
response.data = {
  access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  token_type: "bearer"
}

// Salva no localStorage
localStorage.setItem('token', "eyJhbGci...")
```

### Passo 5: Frontend Busca Informações do Usuário
```javascript
// api.js
GET http://localhost:8000/users/me
Headers: {
  Authorization: "Bearer eyJhbGci..."
}

// Backend valida token
payload = jwt.decode("eyJhbGci...", SECRET_KEY)
# Retorna: { "sub": "admin", "user_id": 1, "role": "admin" }

# Busca usuário
user = db.query(User).filter(User.id == 1).first()

# Retorna
return {
  id: 1,
  username: "admin",
  email: "admin@suvinil.com",
  role: "admin",
  is_active: true
}
```

### Passo 6: Frontend Atualiza Estado
```javascript
// api.js salva
localStorage.setItem('user', JSON.stringify({
  id: 1,
  username: "admin",
  role: "admin"
}))

// AuthContext atualiza
setUser({ id: 1, username: "admin", role: "admin" })
setIsAuthenticated(true)

// Login.jsx redireciona
navigate('/chat')
```

## 🛡️ Como Funciona a Proteção

### Backend: Verificar Token

```python
# dependencies.py
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 1. Decodifica token
    payload = jwt.decode(token, SECRET_KEY)
    # payload = { "sub": "admin", "user_id": 1, "role": "admin" }
    
    # 2. Busca usuário
    user = UserRepository.get_by_username(db, payload["sub"])
    
    # 3. Retorna dados
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }

# Usar em endpoint
@router.get("/users/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # current_user já contém dados do usuário autenticado
    return current_user
```

### Frontend: Interceptor Adiciona Token

```javascript
// api.js
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    // Adiciona token em TODAS as requisições
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Quando você faz:
api.get('/users/me')

// O interceptor transforma em:
GET /users/me
Headers: {
  Authorization: "Bearer eyJhbGci..."
}
```

## 📝 Exemplo Prático Completo

### Criar Usuário no Banco

```python
# Backend
from app.core.security import get_password_hash

hashed = get_password_hash("senha123")
# "$2b$12$LQv3c1yqBWVHxkd0LHAkCO..."

user = User(
    username="joao",
    email="joao@teste.com",
    hashed_password=hashed,
    role=UserRole.USER
)
db.add(user)
db.commit()
```

### Login no Frontend

```javascript
// 1. Usuário preenche
username = "joao"
password = "senha123"

// 2. Frontend envia
POST /auth/login
{ username: "joao", password: "senha123" }

// 3. Backend verifica
verify_password("senha123", "$2b$12$LQv3c1yq...")  // True

// 4. Backend retorna token
{ access_token: "eyJhbGci..." }

// 5. Frontend salva
localStorage.setItem('token', "eyJhbGci...")

// 6. Frontend usa token
GET /users/me
Authorization: Bearer eyJhbGci...
```

## ✅ Checklist de Implementação

### Backend ✅
- [x] Modelo User com hashed_password
- [x] Funções de hash/verificação (bcrypt)
- [x] Funções de JWT (criar/validar)
- [x] Endpoint POST /auth/login
- [x] Dependency get_current_user
- [x] Proteção de rotas

### Frontend ✅
- [x] API client (axios)
- [x] Interceptor para token
- [x] Função authApi.login
- [x] AuthContext
- [x] Página Login
- [x] Armazenamento localStorage

## 🎯 Resumo em 3 Passos

1. **Backend**: Recebe credenciais → Verifica no banco → Gera JWT → Retorna token
2. **Frontend**: Envia credenciais → Recebe token → Salva no localStorage
3. **Uso**: Frontend envia token em todas as requisições → Backend valida token → Permite acesso

## 🔍 Debug

### Ver Token no Console
```javascript
// Ver token
localStorage.getItem('token')

// Decodificar (debug)
const token = localStorage.getItem('token');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log(payload);
// { sub: "admin", user_id: 1, role: "admin", exp: 1234567890 }
```

### Testar Manualmente
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Usar token
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

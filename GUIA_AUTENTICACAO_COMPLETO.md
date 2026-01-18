# 🔐 Guia Completo: Autenticação Backend ↔ Frontend

## 📋 Visão Geral do Fluxo

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ──────> │    Backend   │ ──────> │   Database  │
│  (React)    │         │   (FastAPI)  │         │ (PostgreSQL)│
└─────────────┘         └──────────────┘         └─────────────┘
     │                         │                         │
     │  1. Login Request       │                         │
     ├────────────────────────>│                         │
     │                         │  2. Buscar User         │
     │                         ├────────────────────────>│
     │                         │<────────────────────────┤
     │                         │  3. Verificar Senha     │
     │                         │  4. Gerar JWT Token     │
     │  5. Recebe Token         │                         │
     │<────────────────────────┤                         │
     │  6. Salva Token         │                         │
     │  7. Busca User Info     │                         │
     │<────────────────────────┤                         │
     │                         │                         │
```

## 🏗️ Arquitetura da Autenticação

### 1. Modelo de Dados (Backend)

**Arquivo**: `suvinil-ai/app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # ⚠️ NUNCA armazena senha em texto plano!
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
```

**Pontos Importantes:**
- ✅ `hashed_password`: Senha é armazenada como hash (bcrypt)
- ✅ `is_active`: Permite desativar usuários sem deletar
- ✅ `role`: Define permissões (ADMIN ou USER)

### 2. Segurança (Backend)

**Arquivo**: `suvinil-ai/app/core/security.py`

#### Hash de Senha
```python
def get_password_hash(password: str) -> str:
    """Gera hash da senha usando bcrypt"""
    return pwd_context.hash(password)
    # Exemplo: "senha123" -> "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5..."

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return pwd_context.verify(plain_password, hashed_password)
    # Compara "senha123" com o hash armazenado
```

#### JWT Token
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token JWT com informações do usuário"""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    # Token contém: username, user_id, role, email, exp
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica e valida token JWT"""
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

### 3. Endpoint de Login (Backend)

**Arquivo**: `suvinil-ai/app/api/v1/auth.py`

```python
@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    # 1. Buscar usuário no banco
    user = UserRepository.get_by_username(db, credentials.username)
    
    # 2. Verificar se usuário existe e senha está correta
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(401, "Incorrect username or password")
    
    # 3. Verificar se usuário está ativo
    if not user.is_active:
        raise HTTPException(400, "Inactive user")
    
    # 4. Gerar token JWT
    access_token = create_access_token(
        data={
            "sub": user.username,      # Subject (quem é o usuário)
            "user_id": user.id,        # ID do usuário
            "role": user.role.value,   # Role (admin/user)
            "email": user.email,       # Email
        },
        expires_delta=timedelta(minutes=30)
    )
    
    # 5. Retornar token
    return {"access_token": access_token, "token_type": "bearer"}
```

**Fluxo:**
1. Recebe `username` e `password`
2. Busca usuário no banco
3. Compara senha com hash armazenado
4. Se correto, gera token JWT
5. Retorna token para frontend

### 4. Frontend - API Client

**Arquivo**: `suvinil-frontend/src/lib/api.js`

#### Configuração do Axios
```javascript
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: Adiciona token automaticamente em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

#### Função de Login
```javascript
export const authApi = {
  login: async (username, password) => {
    // 1. Envia credenciais para backend
    const response = await api.post('/auth/login', { username, password });
    
    // 2. Se recebeu token, salva no localStorage
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      
      // 3. Busca informações completas do usuário
      try {
        const userResponse = await api.get('/users/me');
        localStorage.setItem('user', JSON.stringify(userResponse.data));
        return { ...response.data, user: userResponse.data };
      } catch (error) {
        // Se falhar, ainda retorna o token
        return response.data;
      }
    }
    return response.data;
  },
};
```

### 5. Frontend - Context de Autenticação

**Arquivo**: `suvinil-frontend/src/contexts/AuthContext.jsx`

```javascript
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Ao carregar, verifica se há usuário salvo
  useEffect(() => {
    const currentUser = authApi.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
      setIsAuthenticated(true);
    }
  }, []);

  const login = async (username, password) => {
    // Chama API de login
    const response = await authApi.login(username, password);
    
    // Atualiza estado
    const currentUser = authApi.getCurrentUser();
    setUser(currentUser);
    setIsAuthenticated(true);
    
    return response;
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### 6. Frontend - Página de Login

**Arquivo**: `suvinil-frontend/src/pages/Login.jsx`

```javascript
export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      // Chama função de login do contexto
      await login(username, password);
      
      // Redireciona para chat após login bem-sucedido
      navigate('/chat');
    } catch (err) {
      // Mostra erro se login falhar
      setError(err.response?.data?.detail || 'Erro ao fazer login');
    }
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

## 🔄 Fluxo Completo Passo a Passo

### Passo 1: Usuário Preenche Formulário
```
Frontend (Login.jsx)
├─ Usuário digita: username="admin", password="admin123"
└─ Clica em "Entrar"
```

### Passo 2: Frontend Envia Requisição
```javascript
// Login.jsx chama
await login(username, password)

// Que chama
authApi.login(username, password)

// Que faz
POST http://localhost:8000/auth/login
Body: { "username": "admin", "password": "admin123" }
```

### Passo 3: Backend Processa Login
```python
# auth.py recebe
credentials: UserLogin = { username: "admin", password: "admin123" }

# Busca no banco
user = UserRepository.get_by_username(db, "admin")

# Verifica senha
verify_password("admin123", user.hashed_password)  # True

# Gera token
token = create_access_token({
    "sub": "admin",
    "user_id": 1,
    "role": "admin",
    "email": "admin@suvinil.com"
})

# Retorna
{ "access_token": "eyJhbGci...", "token_type": "bearer" }
```

### Passo 4: Frontend Recebe e Armazena Token
```javascript
// api.js recebe resposta
response.data.access_token = "eyJhbGci..."

// Salva no localStorage
localStorage.setItem('token', "eyJhbGci...")

// Busca informações do usuário
GET /users/me
Headers: { Authorization: "Bearer eyJhbGci..." }

// Salva usuário
localStorage.setItem('user', JSON.stringify({
  id: 1,
  username: "admin",
  email: "admin@suvinil.com",
  role: "admin"
}))
```

### Passo 5: Frontend Atualiza Estado
```javascript
// AuthContext atualiza
setUser({ id: 1, username: "admin", role: "admin" })
setIsAuthenticated(true)

// Redireciona
navigate('/chat')
```

### Passo 6: Requisições Futuras
```javascript
// Qualquer requisição futura
api.get('/paints')

// Interceptor adiciona token automaticamente
Headers: {
  Authorization: "Bearer eyJhbGci..."
}
```

## 🔒 Proteção de Rotas no Backend

### Verificar Token em Endpoints Protegidos

```python
# dependencies.py
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 1. Decodifica token
    payload = decode_access_token(token)
    
    # 2. Busca usuário no banco
    user = UserRepository.get_by_username(db, payload["sub"])
    
    # 3. Retorna dados do usuário
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "email": user.email
    }

# Usar em endpoints
@router.get("/users/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # current_user contém dados do usuário autenticado
    return current_user
```

## 🛡️ Proteção de Rotas no Frontend

```javascript
// App.jsx
function PrivateRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) return <div>Carregando...</div>;
  
  // Se não autenticado, redireciona para login
  return isAuthenticated ? children : <Navigate to="/login" />;
}

// Usar
<Route path="/admin" element={
  <PrivateRoute>
    <Admin />
  </PrivateRoute>
} />
```

## 📝 Exemplo Prático Completo

### Backend: Criar Usuário
```python
# 1. Hash da senha
hashed = get_password_hash("senha123")
# Resultado: "$2b$12$LQv3c1yqBWVHxkd0LHAkCO..."

# 2. Criar usuário
user = User(
    username="joao",
    email="joao@teste.com",
    hashed_password=hashed,
    role=UserRole.USER
)
db.add(user)
db.commit()
```

### Frontend: Login
```javascript
// 1. Usuário preenche formulário
username = "joao"
password = "senha123"

// 2. Envia para backend
POST /auth/login
{ username: "joao", password: "senha123" }

// 3. Backend verifica
verify_password("senha123", user.hashed_password)  // True

// 4. Backend retorna token
{ access_token: "eyJhbGci..." }

// 5. Frontend salva
localStorage.setItem('token', "eyJhbGci...")

// 6. Frontend usa token em requisições
GET /users/me
Headers: { Authorization: "Bearer eyJhbGci..." }
```

## 🔍 Debugging

### Verificar Token no Console
```javascript
// Ver token
localStorage.getItem('token')

// Decodificar token (apenas para debug)
const token = localStorage.getItem('token');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log(payload);
// { sub: "admin", user_id: 1, role: "admin", exp: 1234567890 }
```

### Testar Login Manualmente
```bash
# Testar login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Usar token
TOKEN="seu_token_aqui"
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $TOKEN"
```

## ✅ Checklist de Implementação

### Backend
- [x] Modelo User com hashed_password
- [x] Funções de hash/verificação de senha
- [x] Funções de criação/validação de JWT
- [x] Endpoint POST /auth/login
- [x] Dependency para verificar token
- [x] Proteção de rotas com require_role

### Frontend
- [x] API client com axios
- [x] Interceptor para adicionar token
- [x] Função de login
- [x] Context de autenticação
- [x] Página de login
- [x] Proteção de rotas
- [x] Armazenamento de token no localStorage

## 🎯 Resumo

1. **Backend**: Recebe username/password → Verifica no banco → Gera JWT → Retorna token
2. **Frontend**: Envia credenciais → Recebe token → Salva no localStorage → Usa em requisições
3. **Proteção**: Backend valida token em cada requisição → Frontend verifica autenticação antes de renderizar

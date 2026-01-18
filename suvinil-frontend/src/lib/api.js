import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Criar instância do axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratar erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado ou inválido
      const token = localStorage.getItem('token');
      
      // Só limpa e redireciona se havia um token (usuário estava autenticado)
      // Se não havia token, é um endpoint que requer auth mas usuário não está logado
      // Nesse caso, não redireciona automaticamente (permite que o componente trate)
      if (token) {
        console.warn('Token inválido ou expirado. Fazendo logout...');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // Só redireciona se não estiver já na página de login
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      // Se não havia token, apenas rejeita o erro (endpoint pode funcionar sem auth)
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  login: async (username, password) => {
    // OAuth2 espera form-data, não JSON
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      // Buscar informações do usuário usando o token
      try {
        await new Promise(resolve => setTimeout(resolve, 100));
        const userResponse = await api.get('/users/me');
        localStorage.setItem('user', JSON.stringify(userResponse.data));
        return { ...response.data, user: userResponse.data };
      } catch (error) {
        console.error('Error fetching user info:', error);
        if (error.response?.status === 401) {
          console.warn('Token recebido mas não válido para /users/me. Pode ser problema temporário.');
        }
        return response.data;
      }
    }
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
  refreshUser: async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.warn('No token available to refresh user info');
        return null;
      }
      const userResponse = await api.get('/users/me');
      localStorage.setItem('user', JSON.stringify(userResponse.data));
      return userResponse.data;
    } catch (error) {
      console.error('Error refreshing user info:', error);
      // Se for 401, limpa o token inválido
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
      return null;
    }
  },
};

export const chatApi = {
  sendMessage: async (message, resetConversation = false) => {
    // Usa a instância api que já gerencia o token automaticamente
    // Se não houver token, a requisição será feita sem autenticação
    const response = await api.post('/ai/chat', {
      message,
      reset_conversation: resetConversation,
    });
    return response.data;
  },
  resetChat: async () => {
    try {
      const response = await api.post('/ai/chat/reset');
      return response.data;
    } catch (error) {
      // Se não estiver autenticado, ainda funciona
      if (error.response?.status === 401 || error.response?.status === 422) {
        return { response: 'Conversa resetada.' };
      }
      throw error;
    }
  },
};

export const paintsApi = {
  getAll: async (params = {}) => {
    const response = await api.get('/paints', { params });
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/paints/${id}`);
    return response.data;
  },
  create: async (paintData) => {
    const response = await api.post('/paints', paintData);
    return response.data;
  },
  update: async (id, paintData) => {
    const response = await api.put(`/paints/${id}`, paintData);
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/paints/${id}`);
  },
};

export default api;
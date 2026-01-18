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
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      // Buscar informações do usuário usando o token
      try {
        const userResponse = await api.get('/users/me');
        localStorage.setItem('user', JSON.stringify(userResponse.data));
        return { ...response.data, user: userResponse.data };
      } catch (error) {
        console.error('Error fetching user info:', error);
        // Mesmo se falhar, retorna o token
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
      const userResponse = await api.get('/users/me');
      localStorage.setItem('user', JSON.stringify(userResponse.data));
      return userResponse.data;
    } catch (error) {
      console.error('Error refreshing user info:', error);
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
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import api from '../lib/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper para extrair mensagem de erro
const getErrorMessage = (err, defaultMessage) => {
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  } else if (Array.isArray(detail) && detail.length > 0) {
    return detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
  }
  return defaultMessage;
};

export function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validações
    if (formData.password !== formData.confirmPassword) {
      setError('As senhas não coincidem');
      return;
    }

    if (formData.password.length < 6) {
      setError('A senha deve ter pelo menos 6 caracteres');
      return;
    }

    setIsLoading(true);

    try {
      // Chamar endpoint de registro
      const response = await api.post('/auth/register', {
        username: formData.username,
        email: formData.email,
        full_name: formData.full_name,
        password: formData.password,
      });

      // Se registro bem-sucedido, fazer login automático
      if (response.data) {
        // Fazer login automaticamente após registro (usando form-data)
        try {
          const loginFormData = new URLSearchParams();
          loginFormData.append('username', formData.username);
          loginFormData.append('password', formData.password);
          
          const loginResponse = await axios.post(`${API_BASE_URL}/auth/login`, loginFormData, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          });

          if (loginResponse.data.access_token) {
            localStorage.setItem('token', loginResponse.data.access_token);
            
            // Buscar informações do usuário
            try {
              const userResponse = await api.get('/users/me');
              localStorage.setItem('user', JSON.stringify(userResponse.data));
            } catch (err) {
              console.error('Error fetching user info:', err);
            }
          }

          // Redirecionar para chat
          navigate('/chat', { replace: true });
        } catch (loginError) {
          // Se login automático falhar, redireciona para login
          setError('Conta criada com sucesso! Faça login para continuar.');
          setTimeout(() => {
            navigate('/login');
          }, 2000);
        }
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError(getErrorMessage(err, 'Erro ao criar conta. Verifique os dados e tente novamente.'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Criar Conta</CardTitle>
          <CardDescription className="text-center">
            Registre-se para acessar o chatbot inteligente
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="username" className="text-sm font-medium">
                Usuário *
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                placeholder="Digite seu usuário"
                value={formData.username}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email *
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="Digite seu email"
                value={formData.email}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="full_name" className="text-sm font-medium">
                Nome Completo
              </label>
              <Input
                id="full_name"
                name="full_name"
                type="text"
                placeholder="Digite seu nome completo"
                value={formData.full_name}
                onChange={handleChange}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Senha *
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="Digite sua senha (mín. 6 caracteres)"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={isLoading}
                minLength={6}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="text-sm font-medium">
                Confirmar Senha *
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder="Confirme sua senha"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                disabled={isLoading}
                minLength={6}
              />
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Criando conta...' : 'Criar Conta'}
            </Button>

            <div className="text-center text-sm text-muted-foreground">
              Já tem uma conta?{' '}
              <Link
                to="/login"
                className="text-primary hover:underline font-medium"
              >
                Fazer login
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

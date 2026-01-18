import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { paintsApi } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { ArrowLeft, Plus, Edit, Trash2, Search } from 'lucide-react';

export function Admin() {
  const [paints, setPaints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingPaint, setEditingPaint] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color_code: '',
    environment: 'INTERIOR',
    finish_type: 'FOSCO',
    line: 'STANDARD',
    is_active: true,
  });

  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user || !isAdmin()) {
      navigate('/chat');
      return;
    }
    loadPaints();
  }, [user, isAdmin, navigate]);

  const loadPaints = async () => {
    try {
      setIsLoading(true);
      const data = await paintsApi.getAll({ search: searchTerm });
      setPaints(data);
    } catch (error) {
      console.error('Error loading paints:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadPaints();
    }, 300); // Debounce de 300ms para busca
    
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingPaint) {
        await paintsApi.update(editingPaint.id, formData);
      } else {
        await paintsApi.create(formData);
      }
      resetForm();
      loadPaints();
    } catch (error) {
      console.error('Error saving paint:', error);
      alert('Erro ao salvar tinta. Tente novamente.');
    }
  };

  const handleEdit = (paint) => {
    setEditingPaint(paint);
    setFormData({
      name: paint.name || '',
      description: paint.description || '',
      color_code: paint.color_code || '',
      environment: paint.environment || 'INTERIOR',
      finish_type: paint.finish_type || 'FOSCO',
      line: paint.line || 'STANDARD',
      is_active: paint.is_active !== undefined ? paint.is_active : true,
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('Tem certeza que deseja excluir esta tinta?')) return;
    try {
      await paintsApi.delete(id);
      loadPaints();
    } catch (error) {
      console.error('Error deleting paint:', error);
      alert('Erro ao excluir tinta. Tente novamente.');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      color_code: '',
      environment: 'INTERIOR',
      finish_type: 'FOSCO',
      line: 'STANDARD',
      is_active: true,
    });
    setEditingPaint(null);
    setShowForm(false);
  };

  const filteredPaints = paints.filter((paint) =>
    paint.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    paint.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => navigate('/chat')}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-xl font-bold">Gerenciar Catálogo</h1>
          </div>
          <Button variant="outline" onClick={() => { logout(); navigate('/login'); }}>
            Sair
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-4 space-y-4">
        {/* Search and Add */}
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar tintas..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button onClick={() => { resetForm(); setShowForm(true); }}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Tinta
          </Button>
        </div>

        {/* Form */}
        {showForm && (
          <Card>
            <CardHeader>
              <CardTitle>{editingPaint ? 'Editar Tinta' : 'Nova Tinta'}</CardTitle>
              <CardDescription>
                {editingPaint ? 'Atualize as informações da tinta' : 'Adicione uma nova tinta ao catálogo'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Nome *</label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Código de Cor</label>
                    <Input
                      value={formData.color_code}
                      onChange={(e) => setFormData({ ...formData, color_code: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Descrição</label>
                  <textarea
                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Ambiente</label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      value={formData.environment}
                      onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                    >
                      <option value="INTERIOR">Interior</option>
                      <option value="EXTERIOR">Exterior</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Tipo de Acabamento</label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      value={formData.finish_type}
                      onChange={(e) => setFormData({ ...formData, finish_type: e.target.value })}
                    >
                      <option value="FOSCO">Fosco</option>
                      <option value="ACETINADO">Acetinado</option>
                      <option value="BRILHANTE">Brilhante</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Linha</label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      value={formData.line}
                      onChange={(e) => setFormData({ ...formData, line: e.target.value })}
                    >
                      <option value="STANDARD">Standard</option>
                      <option value="PREMIUM">Premium</option>
                      <option value="ECONOMY">Economy</option>
                    </select>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <label htmlFor="is_active" className="text-sm font-medium">
                    Ativo
                  </label>
                </div>
                <div className="flex gap-2">
                  <Button type="submit">
                    {editingPaint ? 'Atualizar' : 'Criar'}
                  </Button>
                  <Button type="button" variant="outline" onClick={resetForm}>
                    Cancelar
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Paints List */}
        {isLoading ? (
          <div className="text-center py-8">Carregando...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredPaints.map((paint) => (
              <Card key={paint.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{paint.name}</CardTitle>
                      {paint.color_code && (
                        <CardDescription>Código: {paint.color_code}</CardDescription>
                      )}
                    </div>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        paint.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {paint.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  {paint.description && (
                    <p className="text-sm text-muted-foreground mb-4">{paint.description}</p>
                  )}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="text-xs bg-secondary px-2 py-1 rounded">
                      {paint.environment}
                    </span>
                    <span className="text-xs bg-secondary px-2 py-1 rounded">
                      {paint.finish_type}
                    </span>
                    <span className="text-xs bg-secondary px-2 py-1 rounded">
                      {paint.line}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(paint)}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Editar
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(paint.id)}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Excluir
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!isLoading && filteredPaints.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            Nenhuma tinta encontrada.
          </div>
        )}
      </div>
    </div>
  );
}
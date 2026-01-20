import { useState, useEffect } from 'react';
import { paintsApi } from '../../lib/api';
import { Modal } from '../ui/Modal';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Input } from '../ui/Input';
import { Loader2, Search } from 'lucide-react';

export function CatalogModal({ isOpen, onClose }) {
  const [paints, setPaints] = useState([]);
  const [filteredPaints, setFilteredPaints] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadPaints();
    }
  }, [isOpen]);

  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredPaints(paints);
      return;
    }

    const term = searchTerm.toLowerCase();
    const filtered = paints.filter((paint) => {
      return (
        paint.nome?.toLowerCase().includes(term) ||
        paint.cor?.toLowerCase().includes(term) ||
        paint.linha?.toLowerCase().includes(term) ||
        paint.aplicacao?.some(app => app.toLowerCase().includes(term)) ||
        paint.features?.some(feat => feat.toLowerCase().includes(term))
      );
    });
    setFilteredPaints(filtered);
  }, [searchTerm, paints]);

  const loadPaints = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await paintsApi.getAll({ limit: 1000 });
      // O endpoint retorna um array diretamente
      const paintsArray = Array.isArray(data) ? data : [];
      setPaints(paintsArray);
      setFilteredPaints(paintsArray);
    } catch (err) {
      console.error('Error loading paints:', err);
      setError('Erro ao carregar o catálogo. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const getAcabamentoLabel = (acabamento) => {
    const labels = {
      FOSCO: 'Fosco',
      ACETINADO: 'Acetinado',
      SEMI_BRILHO: 'Semi-Brilho',
      BRILHO: 'Brilho',
      BRILHANTE: 'Brilhante',
    };
    return labels[acabamento] || acabamento;
  };

  const getAmbienteLabel = (ambiente) => {
    const labels = {
      INTERNO: 'Interno',
      EXTERNO: 'Externo',
      INTERNO_EXTERNO: 'Interno/Externo',
    };
    return labels[ambiente] || ambiente;
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Catálogo Completo de Tintas"
      size="xl"
    >
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-lg">Carregando catálogo...</span>
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <p className="text-destructive text-lg">{error}</p>
        </div>
      )}

      {!isLoading && !error && paints.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground text-lg">
            Nenhuma tinta disponível no catálogo.
          </p>
        </div>
      )}

      {!isLoading && !error && paints.length > 0 && (
        <div>
          {/* Search Bar */}
          <div className="mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Buscar por nome, cor, linha ou características..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              {filteredPaints.length === paints.length
                ? `Total de ${paints.length} tintas disponíveis`
                : `Mostrando ${filteredPaints.length} de ${paints.length} tintas`}
            </p>
          </div>

          {filteredPaints.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground text-lg">
                Nenhuma tinta encontrada com os filtros aplicados.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPaints.map((paint) => (
                <Card key={paint.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">{paint.nome}</CardTitle>
                    <p className="text-sm text-muted-foreground">{paint.linha}</p>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    {paint.cor && (
                      <div>
                        <span className="font-medium">Cor:</span>{' '}
                        <span className="text-muted-foreground">{paint.cor}</span>
                      </div>
                    )}
                    <div>
                      <span className="font-medium">Ambiente:</span>{' '}
                      <span className="text-muted-foreground">
                        {getAmbienteLabel(paint.ambiente)}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium">Acabamento:</span>{' '}
                      <span className="text-muted-foreground">
                        {getAcabamentoLabel(paint.acabamento)}
                      </span>
                    </div>
                    {paint.aplicacao && paint.aplicacao.length > 0 && (
                      <div>
                        <span className="font-medium">Aplicação:</span>{' '}
                        <span className="text-muted-foreground">
                          {paint.aplicacao.join(', ')}
                        </span>
                      </div>
                    )}
                    {paint.features && paint.features.length > 0 && (
                      <div>
                        <span className="font-medium">Características:</span>
                        <ul className="list-disc list-inside text-muted-foreground ml-2 mt-1">
                          {paint.features.slice(0, 3).map((feature, idx) => (
                            <li key={idx} className="text-xs">{feature}</li>
                          ))}
                          {paint.features.length > 3 && (
                            <li className="text-xs italic">
                              +{paint.features.length - 3} mais...
                            </li>
                          )}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

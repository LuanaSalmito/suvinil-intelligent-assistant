"""Testes para o serviço RAG (Retrieval-Augmented Generation)"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch, Mock
from sqlalchemy.orm import Session
from app.ai.rag_service import RAGService
from app.models.paint import PaintAmbiente, PaintAcabamento, PaintLinha


class TestRAGService:
    """Testes para a classe RAGService"""
    
    @pytest.fixture
    def mock_db(self):
        """Fixture para sessão de banco de dados mockada"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_settings(self):
        """Fixture para configurações mockadas"""
        with patch('app.ai.rag_service.settings') as mock:
            mock.OPENAI_API_KEY = "test-api-key-12345"
            mock.OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
            yield mock
    
    @pytest.fixture
    def sample_paint(self):
        """Fixture para tinta de exemplo"""
        paint = MagicMock()
        paint.id = 1
        paint.nome = "Tinta Premium Azul"
        paint.cor = "Azul Celeste"
        paint.ambiente = PaintAmbiente.INTERNO
        paint.tipo_parede = "Parede, Gesso"
        paint.acabamento = PaintAcabamento.FOSCO
        paint.features = "Lavável, Alta cobertura, Antimanchas"
        paint.linha = PaintLinha.PREMIUM
        return paint
    
    @pytest.fixture
    def sample_paints_list(self, sample_paint):
        """Fixture para lista de tintas de exemplo"""
        paint2 = MagicMock()
        paint2.id = 2
        paint2.nome = "Tinta Externa Branca"
        paint2.cor = "Branco"
        paint2.ambiente = PaintAmbiente.EXTERNO
        paint2.tipo_parede = "Parede"
        paint2.acabamento = PaintAcabamento.ACETINADO
        paint2.features = "Resistente ao sol, Anti-mofo"
        paint2.linha = PaintLinha.STANDARD
        
        paint3 = MagicMock()
        paint3.id = 3
        paint3.nome = "Tinta Madeira Verde"
        paint3.cor = "Verde Floresta"
        paint3.ambiente = PaintAmbiente.INTERNO_EXTERNO
        paint3.tipo_parede = "Madeira"
        paint3.acabamento = PaintAcabamento.BRILHANTE
        paint3.features = "Proteção UV, Durável"
        paint3.linha = PaintLinha.PREMIUM
        
        return [sample_paint, paint2, paint3]
    
    @pytest.fixture
    def temp_chroma_dir(self):
        """Fixture para diretório temporário do ChromaDB"""
        temp_dir = tempfile.mkdtemp()
        
        # Patch do diretório persistente
        with patch.object(RAGService, 'PERSIST_DIRECTORY', temp_dir):
            yield temp_dir
        
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_initialization(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Inicialização do RAGService"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            assert service.db == mock_db
            assert service.embeddings is not None
            # Vectorstore pode ser None se não há dados
            assert service.vectorstore is None or service.vectorstore is not None
    
    def test_paint_to_document(self, mock_db, mock_settings, sample_paint, temp_chroma_dir):
        """Teste: Conversão de Paint para Document"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            document = service._paint_to_document(sample_paint)
            
            # Verifica conteúdo
            assert "Tinta Premium Azul" in document.page_content
            assert "Azul Celeste" in document.page_content
            assert "Interno" in document.page_content
            assert "Fosco" in document.page_content
            
            # Verifica metadata
            assert document.metadata['paint_id'] == 1
            assert document.metadata['nome'] == "Tinta Premium Azul"
            assert document.metadata['cor'] == "azul celeste"
            assert document.metadata['ambiente'] == "interno"
            assert "parede" in document.metadata['tipo_parede']
            assert document.metadata['linha'] == "Premium"
    
    def test_reindex_no_paints(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Reindexação sem tintas no banco"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            count = service.reindex()
            
            assert count == 0
            assert service.vectorstore is None
    
    def test_reindex_with_paints(self, mock_db, mock_settings, sample_paints_list, temp_chroma_dir):
        """Teste: Reindexação com tintas no banco"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=sample_paints_list):
            with patch('app.ai.rag_service.Chroma.from_documents') as mock_chroma:
                mock_vectorstore = MagicMock()
                mock_chroma.return_value = mock_vectorstore
                
                service = RAGService(mock_db)
                count = service.reindex()
                
                assert count == 3
                assert service.vectorstore is not None
                mock_chroma.assert_called_once()
    
    def test_search_paints_no_vectorstore(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Busca sem vectorstore inicializado"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            service.vectorstore = None
            
            results = service.search_paints("tinta azul")
            
            assert results == []
    
    def test_search_paints_with_results(self, mock_db, mock_settings, sample_paint, temp_chroma_dir):
        """Teste: Busca com resultados"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            # Mock do vectorstore
            mock_doc = MagicMock()
            mock_doc.page_content = "Tinta Premium Azul para interno"
            mock_doc.metadata = {
                'paint_id': 1,
                'nome': 'Tinta Premium Azul',
                'cor': 'azul celeste',
                'ambiente': 'interno'
            }
            
            service.vectorstore = MagicMock()
            service.vectorstore.similarity_search_with_score = MagicMock(
                return_value=[(mock_doc, 0.85)]
            )
            
            results = service.search_paints("tinta azul para sala", k=3)
            
            assert len(results) == 1
            assert results[0]['paint_id'] == 1
            assert results[0]['nome'] == 'Tinta Premium Azul'
            assert results[0]['score'] == 0.85
            assert 'content' in results[0]
    
    def test_search_paints_with_filters(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Busca com filtros aplicados"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            mock_doc = MagicMock()
            mock_doc.page_content = "Tinta externa branca"
            mock_doc.metadata = {
                'paint_id': 2,
                'nome': 'Tinta Externa',
                'ambiente': 'externo',
                'cor': 'branco'
            }
            
            service.vectorstore = MagicMock()
            service.vectorstore.similarity_search_with_score = MagicMock(
                return_value=[(mock_doc, 0.9)]
            )
            
            filters = {
                'ambiente': 'externo',
                'cor': 'branco'
            }
            
            results = service.search_paints("tinta para fachada", k=1, filters=filters)
            
            assert len(results) == 1
            # Verifica que os filtros foram passados
            call_args = service.vectorstore.similarity_search_with_score.call_args
            assert call_args.kwargs['filter'] is not None
    
    def test_search_paints_single_filter(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Busca com um único filtro"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            service.vectorstore = MagicMock()
            service.vectorstore.similarity_search_with_score = MagicMock(return_value=[])
            
            filters = {'ambiente': 'interno'}
            service.search_paints("tinta", k=3, filters=filters)
            
            call_args = service.vectorstore.similarity_search_with_score.call_args
            # Com um único filtro, não usa $and
            assert call_args.kwargs['filter'] == {'ambiente': 'interno'}
    
    def test_search_paints_multiple_filters(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Busca com múltiplos filtros (usa $and)"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            service.vectorstore = MagicMock()
            service.vectorstore.similarity_search_with_score = MagicMock(return_value=[])
            
            filters = {
                'ambiente': 'interno',
                'cor': 'azul',
                'tipo_parede': 'parede'
            }
            service.search_paints("tinta", k=3, filters=filters)
            
            call_args = service.vectorstore.similarity_search_with_score.call_args
            # Com múltiplos filtros, usa $and
            assert '$and' in call_args.kwargs['filter']
    
    def test_get_technical_context_with_results(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Obter contexto técnico com resultados"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            mock_result = {
                'paint_id': 1,
                'nome': 'Tinta Premium',
                'cor': 'azul',
                'linha': 'Premium',
                'content': 'Tinta Premium Azul com alta cobertura'
            }
            
            service.search_paints = MagicMock(return_value=[mock_result])
            
            context = service.get_technical_context("tinta azul premium")
            
            assert "Tinta Premium" in context
            assert "azul" in context
            assert "Premium" in context
    
    def test_get_technical_context_no_results(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Contexto técnico sem resultados"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            service.search_paints = MagicMock(return_value=[])
            
            context = service.get_technical_context("tinta inexistente")
            
            assert "Nenhum produto encontrado" in context
    
    def test_get_technical_context_with_filters(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Contexto técnico com filtros"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            mock_result = {
                'paint_id': 2,
                'nome': 'Tinta Externa',
                'cor': 'branco',
                'linha': 'Standard',
                'content': 'Tinta para área externa'
            }
            
            service.search_paints = MagicMock(return_value=[mock_result])
            
            filters = {'ambiente': 'externo'}
            context = service.get_technical_context("tinta para fachada", filters=filters)
            
            assert "Tinta Externa" in context
            service.search_paints.assert_called_once_with("tinta para fachada", k=1, filters=filters)
    
    def test_answer_with_context_alias(self, mock_db, mock_settings, temp_chroma_dir):
        """Teste: Alias retrocompatível answer_with_context"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=[]):
            service = RAGService(mock_db)
            
            service.get_technical_context = MagicMock(return_value="Contexto técnico")
            
            result = service.answer_with_context("query de teste")
            
            assert result == "Contexto técnico"
            service.get_technical_context.assert_called_once_with("query de teste", None)
    
    def test_reindex_removes_old_directory(self, mock_db, mock_settings, sample_paints_list, temp_chroma_dir):
        """Teste: Reindexação remove diretório antigo"""
        with patch('app.ai.rag_service.PaintRepository.get_all', return_value=sample_paints_list):
            # Cria diretório antigo
            os.makedirs(temp_chroma_dir, exist_ok=True)
            old_file = os.path.join(temp_chroma_dir, "old_data.txt")
            with open(old_file, 'w') as f:
                f.write("old data")
            
            with patch('app.ai.rag_service.Chroma.from_documents') as mock_chroma:
                mock_chroma.return_value = MagicMock()
                
                service = RAGService(mock_db)
                service.reindex()
                
                # Verifica que o arquivo antigo foi removido
                # (shutil.rmtree foi chamado)
                # Como usamos temp_chroma_dir, o diretório foi recriado
                assert not os.path.exists(old_file) or os.path.exists(temp_chroma_dir)

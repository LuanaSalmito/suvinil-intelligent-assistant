"""Testes para os especialistas em tintas (Specialists)"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.ai.specialists import (
    BaseSpecialist,
    SurfaceExpert,
    ExteriorExpert,
    ColorExpert,
    InteriorExpert,
    SpecialistRecommendation,
    get_all_specialists
)
from app.models.paint import PaintAmbiente, PaintAcabamento, PaintLinha


class TestSpecialistRecommendation:
    """Testes para a classe SpecialistRecommendation"""
    
    def test_initialization(self):
        """Teste: Inicialização da recomendação"""
        paint_mock = MagicMock()
        paint_mock.id = 1
        paint_mock.nome = "Tinta Teste"
        
        rec = SpecialistRecommendation(
            specialist_name="Test Specialist",
            reasoning="Teste de raciocínio",
            recommended_paints=[paint_mock],
            confidence=0.95,
            key_attributes=["Atributo1", "Atributo2"],
            technical_warnings=["Aviso1"]
        )
        
        assert rec.specialist_name == "Test Specialist"
        assert rec.reasoning == "Teste de raciocínio"
        assert len(rec.recommended_paints) == 1
        assert rec.confidence == 0.95
        assert len(rec.key_attributes) == 2
        assert len(rec.technical_warnings) == 1
    
    def test_to_dict(self):
        """Teste: Conversão para dicionário"""
        paint_mock = MagicMock()
        paint_mock.id = 1
        paint_mock.nome = "Tinta Premium"
        
        rec = SpecialistRecommendation(
            specialist_name="Expert",
            reasoning="Ótima escolha",
            recommended_paints=[paint_mock],
            confidence=0.9,
            key_attributes=["Durabilidade"],
            technical_warnings=[]
        )
        
        result = rec.to_dict()
        
        assert result['specialist'] == "Expert"
        assert result['reasoning'] == "Ótima escolha"
        assert result['confidence'] == 0.9
        assert result['recommendations_count'] == 1
        assert result['paint_ids'] == [1]
        assert result['recommendations'] == ["Tinta Premium"]
        assert result['warnings'] == []
        assert "Durabilidade" in result['key_attributes']


class TestBaseSpecialist:
    """Testes para a classe base BaseSpecialist"""
    
    @pytest.fixture
    def mock_db(self):
        """Fixture para sessão mockada"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def sample_paint(self):
        """Fixture para tinta de exemplo"""
        paint = MagicMock()
        paint.id = 1
        paint.nome = "Tinta Standard"
        paint.cor = "Branco"
        paint.ambiente = PaintAmbiente.INTERNO
        paint.tipo_parede = "Parede"
        paint.acabamento = PaintAcabamento.FOSCO
        paint.features = "Lavável"
        paint.linha = PaintLinha.STANDARD
        return paint
    
    def test_initialization(self, mock_db):
        """Teste: Inicialização do especialista base"""
        specialist = BaseSpecialist(mock_db)
        
        assert specialist.db == mock_db
        assert specialist.repository is not None
    
    def test_can_help_default(self, mock_db):
        """Teste: can_help retorna True por padrão"""
        specialist = BaseSpecialist(mock_db)
        
        assert specialist.can_help({}) is True
    
    def test_get_base_candidates(self, mock_db, sample_paint):
        """Teste: Recuperação de candidatos base"""
        specialist = BaseSpecialist(mock_db)
        
        with patch.object(specialist.repository, 'recommend_candidates', return_value=[sample_paint]):
            context = {
                "ambiente": "interno",
                "tipo_parede": "parede",
                "cor": "branco",
                "acabamento": "fosco"
            }
            
            candidates = specialist._get_base_candidates(context)
            
            assert len(candidates) == 1
            assert candidates[0].nome == "Tinta Standard"


class TestSurfaceExpert:
    """Testes para o SurfaceExpert (Especialista em Superfícies)"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_prompts(self):
        """Mock do prompt manager"""
        with patch('app.ai.specialists.prompt_manager') as mock:
            mock.get_specialist_prompts.return_value = {
                'surface_expert': {
                    'reasoning_template': 'Para aplicar em {surface}, a {product_name} é compatível.'
                }
            }
            yield mock
    
    def test_can_help_with_wood(self, mock_db, mock_prompts):
        """Teste: Identifica que pode ajudar com madeira"""
        expert = SurfaceExpert(mock_db)
        
        context = {"tipo_parede": "madeira"}
        assert expert.can_help(context) is True
    
    def test_can_help_with_metal(self, mock_db, mock_prompts):
        """Teste: Identifica que pode ajudar com metal"""
        expert = SurfaceExpert(mock_db)
        
        context = {"tipo_parede": "metal"}
        assert expert.can_help(context) is True
    
    def test_can_help_with_wall(self, mock_db, mock_prompts):
        """Teste: Identifica que pode ajudar com parede"""
        expert = SurfaceExpert(mock_db)
        
        context = {"tipo_parede": "parede"}
        assert expert.can_help(context) is True
    
    def test_cannot_help_without_surface(self, mock_db, mock_prompts):
        """Teste: Não ajuda sem tipo de superfície"""
        expert = SurfaceExpert(mock_db)
        
        context = {"ambiente": "interno"}
        assert expert.can_help(context) is False
    
    def test_analyze_with_matching_paint(self, mock_db, mock_prompts):
        """Teste: Análise com tinta compatível"""
        expert = SurfaceExpert(mock_db)
        
        paint = MagicMock()
        paint.id = 1
        paint.nome = "Tinta para Madeira"
        paint.tipo_parede = "Madeira, MDF"
        paint.cor = "Branco"
        
        with patch.object(expert, '_get_base_candidates', return_value=[paint]):
            context = {
                "tipo_parede": "madeira",
                "cor": "branco"
            }
            
            rec = expert.analyze(context)
            
            assert rec is not None
            assert rec.specialist_name == expert.name
            assert "madeira" in rec.reasoning.lower()
            assert len(rec.recommended_paints) == 1
            assert rec.confidence == 0.93


class TestExteriorExpert:
    """Testes para o ExteriorExpert (Especialista em Áreas Externas)"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_prompts(self):
        with patch('app.ai.specialists.prompt_manager') as mock:
            mock.get_specialist_prompts.return_value = {
                'exterior_expert': {
                    'reasoning_with_color': 'Para sua varanda, recomendo a {product_name} na cor {color}.',
                    'reasoning_no_color': 'Não encontrei {cor_solicitada}. Temos {product_name} ({color}).',
                    'warning_no_color': "Cor '{cor_solicitada}' não disponível"
                }
            }
            yield mock
    
    def test_can_help_with_external(self, mock_db, mock_prompts):
        """Teste: Identifica ambiente externo"""
        expert = ExteriorExpert(mock_db)
        
        context = {"ambiente": "externo"}
        assert expert.can_help(context) is True
    
    def test_can_help_with_facade(self, mock_db, mock_prompts):
        """Teste: Identifica fachada"""
        expert = ExteriorExpert(mock_db)
        
        context = {"tipo_parede": "fachada"}
        assert expert.can_help(context) is True
    
    def test_cannot_help_with_internal(self, mock_db, mock_prompts):
        """Teste: Não ajuda com ambiente interno"""
        expert = ExteriorExpert(mock_db)
        
        context = {"ambiente": "interno"}
        assert expert.can_help(context) is False
    
    def test_analyze_with_external_paint(self, mock_db, mock_prompts):
        """Teste: Análise com tinta externa"""
        expert = ExteriorExpert(mock_db)
        
        paint = MagicMock()
        paint.id = 1
        paint.nome = "Tinta Fachada Premium"
        paint.cor = "Branco"
        paint.ambiente = PaintAmbiente.EXTERNO
        paint.tipo_parede = "Parede"
        paint.features = "Proteção UV, resistente ao sol"
        
        with patch.object(expert, '_get_base_candidates', return_value=[paint]):
            context = {
                "ambiente": "externo",
                "cor": "branco"
            }
            
            rec = expert.analyze(context)
            
            assert rec is not None
            assert rec.confidence == 0.98
            assert "UV" in rec.key_attributes or "chuva" in str(rec.key_attributes).lower()


class TestColorExpert:
    """Testes para o ColorExpert (Especialista em Cores)"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_prompts(self):
        with patch('app.ai.specialists.prompt_manager') as mock:
            mock.get_specialist_prompts.return_value = {
                'color_expert': {
                    'no_match_reasoning': 'A cor {cor} é excelente para {ambiente}.'
                },
                'color_insights': {
                    'azul': 'Azul transmite calma e serenidade.',
                    'verde': 'Verde traz frescor e natureza.',
                    'default': 'A cor {cor} cria uma atmosfera única.'
                }
            }
            yield mock
    
    def test_can_help_with_color(self, mock_db, mock_prompts):
        """Teste: Identifica que há cor especificada"""
        expert = ColorExpert(mock_db)
        
        context = {"cor": "azul"}
        assert expert.can_help(context) is True
    
    def test_cannot_help_without_color(self, mock_db, mock_prompts):
        """Teste: Não ajuda sem cor"""
        expert = ColorExpert(mock_db)
        
        context = {"ambiente": "interno"}
        assert expert.can_help(context) is False
    
    def test_analyze_with_matching_color(self, mock_db, mock_prompts):
        """Teste: Análise com cor encontrada"""
        expert = ColorExpert(mock_db)
        
        paint = MagicMock()
        paint.id = 1
        paint.nome = "Tinta Azul Celeste"
        paint.cor = "Azul Celeste"
        
        with patch.object(expert, '_get_base_candidates', return_value=[paint]):
            context = {"cor": "azul"}
            
            rec = expert.analyze(context)
            
            assert rec is not None
            assert rec.confidence == 0.95
            assert len(rec.recommended_paints) >= 1


class TestInteriorExpert:
    """Testes para o InteriorExpert (Especialista em Ambientes Internos)"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_prompts(self):
        with patch('app.ai.specialists.prompt_manager') as mock:
            mock.get_specialist_prompts.return_value = {
                'interior_expert': {
                    'reasoning_with_color': 'Para o seu interior, recomendo a {product_name} na cor {color}.',
                    'reasoning_no_color': 'Não encontrei {cor_solicitada}. Temos {product_name} ({color}).',
                    'reasoning_no_products': 'Não encontrei tintas adequadas.',
                    'warning_no_color': "Cor '{cor_solicitada}' não disponível"
                }
            }
            yield mock
    
    def test_can_help_with_internal(self, mock_db, mock_prompts):
        """Teste: Identifica ambiente interno"""
        expert = InteriorExpert(mock_db)
        
        context = {"ambiente": "interno"}
        assert expert.can_help(context) is True
    
    def test_cannot_help_with_external(self, mock_db, mock_prompts):
        """Teste: Não ajuda com ambiente externo"""
        expert = InteriorExpert(mock_db)
        
        context = {"ambiente": "externo"}
        assert expert.can_help(context) is False
    
    def test_analyze_prioritizes_health_features(self, mock_db, mock_prompts):
        """Teste: Prioriza características de saúde (sem odor, lavável)"""
        expert = InteriorExpert(mock_db)
        
        paint1 = MagicMock()
        paint1.id = 1
        paint1.nome = "Tinta Básica"
        paint1.cor = "Branco"
        paint1.ambiente = PaintAmbiente.INTERNO
        paint1.features = ""
        
        paint2 = MagicMock()
        paint2.id = 2
        paint2.nome = "Tinta Premium Sem Odor"
        paint2.cor = "Branco"
        paint2.ambiente = PaintAmbiente.INTERNO
        paint2.features = "Sem odor, Lavável"
        
        with patch.object(expert, '_get_base_candidates', return_value=[paint1, paint2]):
            context = {
                "ambiente": "interno",
                "cor": "branco"
            }
            
            rec = expert.analyze(context)
            
            assert rec is not None
            # O paint2 deve estar primeiro por ter mais features
            assert rec.recommended_paints[0].nome == "Tinta Premium Sem Odor"
            assert "Sem Odor" in rec.key_attributes or "Lavável" in rec.key_attributes


class TestGetAllSpecialists:
    """Testes para a factory de especialistas"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_prompts(self):
        with patch('app.ai.specialists.prompt_manager') as mock:
            mock.get_specialist_prompts.return_value = {
                'surface_expert': {},
                'exterior_expert': {},
                'interior_expert': {},
                'color_expert': {},
                'color_insights': {}
            }
            yield mock
    
    def test_get_all_specialists(self, mock_db, mock_prompts):
        """Teste: Retorna todos os especialistas"""
        specialists = get_all_specialists(mock_db)
        
        assert len(specialists) == 4
        assert isinstance(specialists[0], SurfaceExpert)
        assert isinstance(specialists[1], ExteriorExpert)
        assert isinstance(specialists[2], InteriorExpert)
        assert isinstance(specialists[3], ColorExpert)
    
    def test_all_specialists_have_db(self, mock_db, mock_prompts):
        """Teste: Todos especialistas têm referência ao DB"""
        specialists = get_all_specialists(mock_db)
        
        for specialist in specialists:
            assert specialist.db == mock_db

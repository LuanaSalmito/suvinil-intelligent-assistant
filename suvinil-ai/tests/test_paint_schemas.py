"""Testes unitários para schemas de tinta"""
import pytest
from pydantic import ValidationError
from app.schemas.paint import (
    PaintCreate,
    PaintUpdate,
    Paint,
    PaintCount
)
from app.models.paint import Ambiente, Acabamento, Linha


class TestPaintCreate:
    """Testes para schema PaintCreate"""
    
    def test_paint_create_valid_data(self, sample_paint_data):
        """Testa criação de tinta com dados válidos"""
        paint = PaintCreate(**sample_paint_data)
        
        assert paint.nome == sample_paint_data["nome"]
        assert paint.cor == sample_paint_data["cor"]
        assert paint.ambiente == Ambiente.INTERNO
        assert paint.acabamento == Acabamento.FOSCO
        assert paint.linha == Linha.PREMIUM
    
    def test_paint_create_missing_required_fields(self):
        """Testa criação de tinta sem campos obrigatórios"""
        with pytest.raises(ValidationError):
            PaintCreate(nome="Tinta Teste")
    
    def test_paint_create_invalid_ambiente(self, sample_paint_data):
        """Testa criação com ambiente inválido"""
        sample_paint_data["ambiente"] = "InvalidAmbiente"
        
        with pytest.raises(ValidationError) as exc_info:
            PaintCreate(**sample_paint_data)
        
        assert "ambiente" in str(exc_info.value).lower()
    
    def test_paint_create_invalid_acabamento(self, sample_paint_data):
        """Testa criação com acabamento inválido"""
        sample_paint_data["acabamento"] = "InvalidAcabamento"
        
        with pytest.raises(ValidationError) as exc_info:
            PaintCreate(**sample_paint_data)
        
        assert "acabamento" in str(exc_info.value).lower()
    
    def test_paint_create_without_optional_fields(self):
        """Testa criação de tinta sem campos opcionais"""
        paint_data = {
            "nome": "Tinta Básica",
            "ambiente": "Interno",
            "acabamento": "Fosco",
            "linha": "Standard"
        }
        paint = PaintCreate(**paint_data)
        
        assert paint.nome == "Tinta Básica"
        assert paint.cor is None
        assert paint.tipo_parede is None
        assert paint.features is None


class TestPaintUpdate:
    """Testes para schema PaintUpdate"""
    
    def test_paint_update_partial_data(self):
        """Testa atualização parcial de tinta"""
        update_data = {"cor": "Azul"}
        paint_update = PaintUpdate(**update_data)
        
        assert paint_update.cor == "Azul"
        assert paint_update.nome is None
        assert paint_update.ambiente is None
    
    def test_paint_update_change_ambiente(self):
        """Testa mudança de ambiente"""
        update_data = {"ambiente": Ambiente.EXTERNO}
        paint_update = PaintUpdate(**update_data)
        
        assert paint_update.ambiente == Ambiente.EXTERNO
    
    def test_paint_update_deactivate(self):
        """Testa desativação de tinta"""
        update_data = {"is_active": False}
        paint_update = PaintUpdate(**update_data)
        
        assert paint_update.is_active is False
    
    def test_paint_update_all_fields_optional(self):
        """Testa que todos os campos são opcionais em update"""
        paint_update = PaintUpdate()
        
        assert paint_update.nome is None
        assert paint_update.cor is None
        assert paint_update.ambiente is None


class TestPaintSchema:
    """Testes para schema Paint (resposta)"""
    
    def test_paint_parse_features_from_string(self):
        """Testa conversão de features de string para lista"""
        paint_data = {
            "id": 1,
            "nome": "Tinta Premium",
            "ambiente": "Interno",
            "acabamento": "Fosco",
            "linha": "Premium",
            "is_active": True,
            "features": "Lavável, Alta cobertura, Antimanchas"
        }
        paint = Paint(**paint_data)
        
        assert isinstance(paint.features, list)
        assert len(paint.features) == 3
        assert "Lavável" in paint.features
        assert "Alta cobertura" in paint.features
        assert "Antimanchas" in paint.features
    
    def test_paint_parse_features_from_list(self):
        """Testa que features já em lista são mantidas"""
        paint_data = {
            "id": 1,
            "nome": "Tinta Premium",
            "ambiente": "Interno",
            "acabamento": "Fosco",
            "linha": "Premium",
            "is_active": True,
            "features": ["Lavável", "Alta cobertura"]
        }
        paint = Paint(**paint_data)
        
        assert isinstance(paint.features, list)
        assert len(paint.features) == 2
        assert "Lavável" in paint.features
    
    def test_paint_parse_features_none(self):
        """Testa features None retorna lista vazia"""
        paint_data = {
            "id": 1,
            "nome": "Tinta Básica",
            "ambiente": "Interno",
            "acabamento": "Fosco",
            "linha": "Standard",
            "is_active": True,
            "features": None
        }
        paint = Paint(**paint_data)
        
        assert paint.features == []
    
    def test_paint_populate_aplicacao_from_tipo_parede(self):
        """Testa população automática de aplicacao a partir de tipo_parede"""
        paint_data = {
            "id": 1,
            "nome": "Tinta Multiuso",
            "tipo_parede": "Alvenaria, Gesso, Madeira",
            "ambiente": "Interno",
            "acabamento": "Fosco",
            "linha": "Standard",
            "is_active": True
        }
        paint = Paint(**paint_data)
        
        assert isinstance(paint.aplicacao, list)
        assert len(paint.aplicacao) == 3
        assert "Alvenaria" in paint.aplicacao
        assert "Gesso" in paint.aplicacao
        assert "Madeira" in paint.aplicacao
    
    def test_paint_aplicacao_empty_when_no_tipo_parede(self):
        """Testa que aplicacao fica vazia sem tipo_parede"""
        paint_data = {
            "id": 1,
            "nome": "Tinta Básica",
            "ambiente": "Interno",
            "acabamento": "Fosco",
            "linha": "Standard",
            "is_active": True
        }
        paint = Paint(**paint_data)
        
        assert paint.aplicacao == []


class TestPaintCount:
    """Testes para schema PaintCount"""
    
    def test_paint_count_valid(self):
        """Testa criação de PaintCount"""
        count = PaintCount(total=42)
        
        assert count.total == 42
    
    def test_paint_count_zero(self):
        """Testa PaintCount com zero"""
        count = PaintCount(total=0)
        
        assert count.total == 0

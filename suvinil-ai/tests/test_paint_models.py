"""Testes unitários para models de tinta"""
import pytest
from app.models.paint import (
    Ambiente,
    Acabamento,
    Linha,
    Environment,
    FinishType,
    PaintLine
)


class TestAmbienteEnum:
    """Testes para enum Ambiente"""
    
    def test_ambiente_values(self):
        """Testa valores válidos de Ambiente"""
        assert Ambiente.INTERNO.value == "Interno"
        assert Ambiente.EXTERNO.value == "Externo"
        assert Ambiente.INTERNO_EXTERNO.value == "Interno/Externo"
    
    def test_ambiente_string_comparison(self):
        """Testa comparação de Ambiente com string"""
        assert Ambiente.INTERNO == "Interno"
        assert Ambiente.EXTERNO == "Externo"
    
    def test_ambiente_from_string(self):
        """Testa criação de Ambiente a partir de string"""
        ambiente = Ambiente("Interno")
        assert ambiente == Ambiente.INTERNO
        
        ambiente_externo = Ambiente("Externo")
        assert ambiente_externo == Ambiente.EXTERNO
    
    def test_ambiente_invalid_value(self):
        """Testa valor inválido para Ambiente"""
        with pytest.raises(ValueError):
            Ambiente("InvalidValue")
    
    def test_ambiente_all_members(self):
        """Testa que todos os membros esperados existem"""
        members = [e.value for e in Ambiente]
        assert len(members) == 3
        assert "Interno" in members
        assert "Externo" in members
        assert "Interno/Externo" in members


class TestAcabamentoEnum:
    """Testes para enum Acabamento"""
    
    def test_acabamento_values(self):
        """Testa valores válidos de Acabamento"""
        assert Acabamento.FOSCO.value == "Fosco"
        assert Acabamento.ACETINADO.value == "Acetinado"
        assert Acabamento.BRILHANTE.value == "Brilhante"
    
    def test_acabamento_string_comparison(self):
        """Testa comparação de Acabamento com string"""
        assert Acabamento.FOSCO == "Fosco"
        assert Acabamento.ACETINADO == "Acetinado"
        assert Acabamento.BRILHANTE == "Brilhante"
    
    def test_acabamento_from_string(self):
        """Testa criação de Acabamento a partir de string"""
        acabamento = Acabamento("Fosco")
        assert acabamento == Acabamento.FOSCO
    
    def test_acabamento_invalid_value(self):
        """Testa valor inválido para Acabamento"""
        with pytest.raises(ValueError):
            Acabamento("InvalidValue")
    
    def test_acabamento_all_members(self):
        """Testa que todos os membros esperados existem"""
        members = [e.value for e in Acabamento]
        assert len(members) == 3
        assert "Fosco" in members
        assert "Acetinado" in members
        assert "Brilhante" in members


class TestLinhaEnum:
    """Testes para enum Linha"""
    
    def test_linha_values(self):
        """Testa valores válidos de Linha"""
        assert Linha.PREMIUM.value == "Premium"
        assert Linha.STANDARD.value == "Standard"
    
    def test_linha_string_comparison(self):
        """Testa comparação de Linha com string"""
        assert Linha.PREMIUM == "Premium"
        assert Linha.STANDARD == "Standard"
    
    def test_linha_from_string(self):
        """Testa criação de Linha a partir de string"""
        linha = Linha("Premium")
        assert linha == Linha.PREMIUM
        
        linha_standard = Linha("Standard")
        assert linha_standard == Linha.STANDARD
    
    def test_linha_invalid_value(self):
        """Testa valor inválido para Linha"""
        with pytest.raises(ValueError):
            Linha("InvalidValue")
    
    def test_linha_all_members(self):
        """Testa que todos os membros esperados existem"""
        members = [e.value for e in Linha]
        assert len(members) == 2
        assert "Premium" in members
        assert "Standard" in members


class TestEnumAliases:
    """Testes para aliases de enums"""
    
    def test_environment_alias(self):
        """Testa que Environment é alias de Ambiente"""
        assert Environment is Ambiente
        assert Environment.INTERNO == Ambiente.INTERNO
    
    def test_finish_type_alias(self):
        """Testa que FinishType é alias de Acabamento"""
        assert FinishType is Acabamento
        assert FinishType.FOSCO == Acabamento.FOSCO
    
    def test_paint_line_alias(self):
        """Testa que PaintLine é alias de Linha"""
        assert PaintLine is Linha
        assert PaintLine.PREMIUM == Linha.PREMIUM

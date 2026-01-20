"""Testes unitários para configurações"""
import pytest
import os
from app.core.config import Settings


class TestSettings:
    """Testes para configurações da aplicação"""
    
    def test_settings_default_values(self, test_settings):
        """Testa valores padrão das configurações"""
        assert test_settings.DATABASE_URL == "postgresql://test:test@localhost:5432/test_db"
        assert test_settings.ALGORITHM == "HS256"
        assert test_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    
    def test_settings_secret_key_length(self, test_settings):
        """Testa que a SECRET_KEY tem tamanho mínimo adequado"""
        assert len(test_settings.SECRET_KEY) >= 32
    
    def test_settings_algorithm_is_hs256(self, test_settings):
        """Testa que o algoritmo JWT é HS256"""
        assert test_settings.ALGORITHM == "HS256"
    
    def test_settings_access_token_expiry_positive(self, test_settings):
        """Testa que o tempo de expiração do token é positivo"""
        assert test_settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    def test_settings_openai_model_configuration(self, test_settings):
        """Testa configurações de modelos OpenAI"""
        assert test_settings.OPENAI_CHAT_MODEL is not None
        assert test_settings.OPENAI_EMBEDDING_MODEL is not None
    
    def test_settings_environment_configuration(self, test_settings):
        """Testa configurações de ambiente"""
        assert test_settings.ENVIRONMENT == "test"
        assert test_settings.DEBUG is True
    
    def test_settings_custom_values(self):
        """Testa criação de Settings com valores customizados"""
        custom_settings = Settings(
            DATABASE_URL="postgresql://custom:pass@localhost:5432/custom_db",
            SECRET_KEY="custom-secret-key-with-32-chars-minimum",
            ACCESS_TOKEN_EXPIRE_MINUTES=60,
            ENVIRONMENT="production",
            DEBUG=False
        )
        
        assert custom_settings.DATABASE_URL == "postgresql://custom:pass@localhost:5432/custom_db"
        assert custom_settings.SECRET_KEY == "custom-secret-key-with-32-chars-minimum"
        assert custom_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert custom_settings.ENVIRONMENT == "production"
        assert custom_settings.DEBUG is False
    
    def test_settings_openai_api_key_optional(self):
        """Testa que OPENAI_API_KEY é opcional"""
        settings = Settings(
            SECRET_KEY="test-secret-key-with-32-chars-minimum",
            OPENAI_API_KEY=None
        )
        
        assert settings.OPENAI_API_KEY is None
    
    def test_settings_database_url_format(self, test_settings):
        """Testa formato da URL do banco de dados"""
        assert test_settings.DATABASE_URL.startswith("postgresql://")
    
    def test_settings_default_openai_models(self):
        """Testa modelos padrão do OpenAI"""
        settings = Settings(
            SECRET_KEY="test-secret-key-with-32-chars-minimum"
        )
        
        assert settings.OPENAI_CHAT_MODEL == "gpt-4o-mini"
        assert settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"

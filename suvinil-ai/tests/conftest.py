"""Configurações compartilhadas para testes"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import timedelta
from app.core.config import Settings


@pytest.fixture
def test_settings():
    """Fixture para configurações de teste"""
    return Settings(
        DATABASE_URL="postgresql://test:test@localhost:5432/test_db",
        SECRET_KEY="test-secret-key-with-minimum-32-characters-required",
        ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        OPENAI_API_KEY="test-key",
        ENVIRONMENT="test",
        DEBUG=True
    )


@pytest.fixture
def sample_user_data():
    """Fixture com dados de usuário de exemplo"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "SecurePassword123!"
    }


@pytest.fixture
def sample_paint_data():
    """Fixture com dados de tinta de exemplo"""
    return {
        "nome": "Tinta Premium Branca",
        "cor": "Branco",
        "tipo_parede": "Alvenaria, Gesso",
        "ambiente": "Interno",
        "acabamento": "Fosco",
        "features": "Lavável, Alta cobertura, Antimanchas",
        "linha": "Premium"
    }


@pytest.fixture
def token_expiry():
    """Fixture para tempo de expiração de token de teste"""
    return timedelta(minutes=15)

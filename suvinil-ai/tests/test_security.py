"""Testes unitários para módulo de segurança"""
import pytest
from datetime import timedelta
from jose import jwt
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)
from app.core.config import settings


class TestPasswordHashing:
    """Testes para hash de senhas"""
    
    def test_get_password_hash_creates_hash(self):
        """Testa se get_password_hash cria um hash válido"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_get_password_hash_strips_whitespace(self):
        """Testa se get_password_hash remove espaços em branco"""
        password = "  SecurePassword123!  "
        hashed1 = get_password_hash(password)
        hashed2 = get_password_hash(password.strip())
        
        # Ambos devem gerar hashes válidos para a mesma senha sem espaços
        assert verify_password("SecurePassword123!", hashed1)
        assert verify_password("SecurePassword123!", hashed2)
    
    def test_get_password_hash_truncates_long_passwords(self):
        """Testa se senhas muito longas são truncadas (bcrypt limita em 72 bytes)"""
        long_password = "a" * 100
        hashed = get_password_hash(long_password)
        
        # Deve aceitar a senha truncada
        assert verify_password("a" * 72, hashed)
        assert hashed is not None


class TestPasswordVerification:
    """Testes para verificação de senhas"""
    
    def test_verify_password_correct_password(self):
        """Testa verificação com senha correta"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect_password(self):
        """Testa verificação com senha incorreta"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password("WrongPassword", hashed) is False
    
    def test_verify_password_strips_whitespace(self):
        """Testa se verify_password remove espaços em branco"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password("  SecurePassword123!  ", hashed) is True


class TestJWTTokens:
    """Testes para tokens JWT"""
    
    def test_create_access_token_default_expiry(self):
        """Testa criação de token com expiração padrão"""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verifica se o token pode ser decodificado
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 1
        assert "exp" in payload
    
    def test_create_access_token_custom_expiry(self):
        """Testa criação de token com expiração customizada"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expires_delta)
        
        assert token is not None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "testuser"
    
    def test_decode_access_token_valid(self):
        """Testa decodificação de token válido"""
        data = {"sub": "testuser", "user_id": 1, "role": "user"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == 1
        assert decoded["role"] == "user"
        assert "exp" in decoded
    
    def test_decode_access_token_invalid(self):
        """Testa decodificação de token inválido"""
        invalid_token = "invalid.token.here"
        
        decoded = decode_access_token(invalid_token)
        
        assert decoded is None
    
    def test_decode_access_token_tampered(self):
        """Testa decodificação de token adulterado"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Adultera o token mudando um caractere
        tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")
        
        decoded = decode_access_token(tampered_token)
        
        assert decoded is None

"""Testes unitários para schemas de usuário"""
import pytest
from pydantic import ValidationError
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserInDB,
    UserLogin,
    Token,
    TokenData
)
from app.models.user import UserRole


class TestUserCreate:
    """Testes para schema UserCreate"""
    
    def test_user_create_valid_data(self, sample_user_data):
        """Testa criação de usuário com dados válidos"""
        user = UserCreate(**sample_user_data)
        
        assert user.email == sample_user_data["email"]
        assert user.username == sample_user_data["username"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.password == sample_user_data["password"]
        assert user.role == UserRole.USER
    
    def test_user_create_admin_role(self, sample_user_data):
        """Testa criação de usuário com role admin"""
        sample_user_data["role"] = UserRole.ADMIN
        user = UserCreate(**sample_user_data)
        
        assert user.role == UserRole.ADMIN
    
    def test_user_create_invalid_email(self, sample_user_data):
        """Testa criação de usuário com email inválido"""
        sample_user_data["email"] = "invalid-email"
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**sample_user_data)
        
        assert "email" in str(exc_info.value).lower()
    
    def test_user_create_missing_required_fields(self):
        """Testa criação de usuário sem campos obrigatórios"""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")
    
    def test_user_create_without_full_name(self, sample_user_data):
        """Testa criação de usuário sem full_name (campo opcional)"""
        del sample_user_data["full_name"]
        user = UserCreate(**sample_user_data)
        
        assert user.full_name is None
        assert user.email == sample_user_data["email"]


class TestUserUpdate:
    """Testes para schema UserUpdate"""
    
    def test_user_update_partial_data(self):
        """Testa atualização parcial de usuário"""
        update_data = {"full_name": "Updated Name"}
        user_update = UserUpdate(**update_data)
        
        assert user_update.full_name == "Updated Name"
        assert user_update.email is None
        assert user_update.username is None
    
    def test_user_update_change_role(self):
        """Testa mudança de role do usuário"""
        update_data = {"role": UserRole.ADMIN}
        user_update = UserUpdate(**update_data)
        
        assert user_update.role == UserRole.ADMIN
    
    def test_user_update_deactivate_user(self):
        """Testa desativação de usuário"""
        update_data = {"is_active": False}
        user_update = UserUpdate(**update_data)
        
        assert user_update.is_active is False
    
    def test_user_update_change_password(self):
        """Testa mudança de senha"""
        update_data = {"password": "NewSecurePassword123!"}
        user_update = UserUpdate(**update_data)
        
        assert user_update.password == "NewSecurePassword123!"


class TestUserLogin:
    """Testes para schema UserLogin"""
    
    def test_user_login_valid(self):
        """Testa schema de login com dados válidos"""
        login_data = {
            "username": "testuser",
            "password": "SecurePassword123!"
        }
        user_login = UserLogin(**login_data)
        
        assert user_login.username == "testuser"
        assert user_login.password == "SecurePassword123!"
    
    def test_user_login_missing_fields(self):
        """Testa schema de login sem campos obrigatórios"""
        with pytest.raises(ValidationError):
            UserLogin(username="testuser")


class TestToken:
    """Testes para schema Token"""
    
    def test_token_valid(self):
        """Testa criação de token com dados válidos"""
        token_data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
        token = Token(**token_data)
        
        assert token.access_token == token_data["access_token"]
        assert token.token_type == "bearer"
    
    def test_token_default_type(self):
        """Testa tipo padrão do token"""
        token = Token(access_token="test_token")
        
        assert token.token_type == "bearer"


class TestTokenData:
    """Testes para schema TokenData"""
    
    def test_token_data_complete(self):
        """Testa TokenData com todos os campos"""
        token_data = TokenData(
            username="testuser",
            user_id=1,
            role=UserRole.USER
        )
        
        assert token_data.username == "testuser"
        assert token_data.user_id == 1
        assert token_data.role == UserRole.USER
    
    def test_token_data_optional_fields(self):
        """Testa TokenData com campos opcionais vazios"""
        token_data = TokenData()
        
        assert token_data.username is None
        assert token_data.user_id is None
        assert token_data.role is None

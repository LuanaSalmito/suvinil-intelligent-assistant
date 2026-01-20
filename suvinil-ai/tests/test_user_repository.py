"""Testes unitários para repositório de usuários"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User, UserRole


class TestUserRepositoryGetMethods:
    """Testes para métodos GET do repositório"""
    
    def test_get_by_id_found(self):
        """Testa busca de usuário por ID quando encontrado"""
        mock_db = Mock()
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            is_active=True,
            role=UserRole.USER
        )
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        
        result = UserRepository.get_by_id(mock_db, 1)
        
        assert result is not None
        assert result.id == 1
        assert result.email == "test@example.com"
        mock_db.query.assert_called_once_with(User)
    
    def test_get_by_id_not_found(self):
        """Testa busca de usuário por ID quando não encontrado"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = UserRepository.get_by_id(mock_db, 999)
        
        assert result is None
    
    def test_get_by_email_found(self):
        """Testa busca de usuário por email quando encontrado"""
        mock_db = Mock()
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            is_active=True,
            role=UserRole.USER
        )
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        
        result = UserRepository.get_by_email(mock_db, "test@example.com")
        
        assert result is not None
        assert result.email == "test@example.com"
    
    def test_get_by_username_found(self):
        """Testa busca de usuário por username quando encontrado"""
        mock_db = Mock()
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            is_active=True,
            role=UserRole.USER
        )
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        
        result = UserRepository.get_by_username(mock_db, "testuser")
        
        assert result is not None
        assert result.username == "testuser"
    
    def test_get_all_with_pagination(self):
        """Testa listagem de todos os usuários com paginação"""
        mock_db = Mock()
        mock_users = [
            User(id=1, email="user1@example.com", username="user1", 
                 hashed_password="hash1", is_active=True, role=UserRole.USER),
            User(id=2, email="user2@example.com", username="user2", 
                 hashed_password="hash2", is_active=True, role=UserRole.USER),
        ]
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_users
        
        result = UserRepository.get_all(mock_db, skip=0, limit=10)
        
        assert len(result) == 2
        assert result[0].username == "user1"
        assert result[1].username == "user2"
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(10)


class TestUserRepositoryCreateMethod:
    """Testes para método CREATE do repositório"""
    
    @patch('app.repositories.user_repository.get_password_hash')
    def test_create_user_success(self, mock_hash):
        """Testa criação de usuário com sucesso"""
        mock_hash.return_value = "hashed_password"
        mock_db = Mock()
        
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="SecurePassword123!",
            full_name="New User",
            role=UserRole.USER
        )
        
        # Mock para simular o refresh que popula o ID
        def mock_refresh(user):
            user.id = 1
        
        mock_db.refresh.side_effect = mock_refresh
        
        result = UserRepository.create(mock_db, user_data)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        mock_hash.assert_called_once_with("SecurePassword123!")
    
    @patch('app.repositories.user_repository.get_password_hash')
    def test_create_user_admin_role(self, mock_hash):
        """Testa criação de usuário com role admin"""
        mock_hash.return_value = "hashed_password"
        mock_db = Mock()
        
        user_data = UserCreate(
            email="admin@example.com",
            username="admin",
            password="AdminPass123!",
            role=UserRole.ADMIN
        )
        
        def mock_refresh(user):
            user.id = 1
        
        mock_db.refresh.side_effect = mock_refresh
        
        result = UserRepository.create(mock_db, user_data)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestUserRepositoryUpdateMethod:
    """Testes para método UPDATE do repositório"""
    
    @patch('app.repositories.user_repository.get_password_hash')
    def test_update_user_success(self, mock_hash):
        """Testa atualização de usuário com sucesso"""
        mock_hash.return_value = "new_hashed_password"
        mock_db = Mock()
        mock_user = User(
            id=1,
            email="old@example.com",
            username="olduser",
            hashed_password="old_hash",
            full_name="Old Name",
            is_active=True,
            role=UserRole.USER
        )
        
        # Mock get_by_id
        with patch.object(UserRepository, 'get_by_id', return_value=mock_user):
            update_data = UserUpdate(
                email="new@example.com",
                full_name="New Name"
            )
            
            result = UserRepository.update(mock_db, 1, update_data)
            
            assert result is not None
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    def test_update_user_not_found(self):
        """Testa atualização de usuário não encontrado"""
        mock_db = Mock()
        
        with patch.object(UserRepository, 'get_by_id', return_value=None):
            update_data = UserUpdate(full_name="New Name")
            
            result = UserRepository.update(mock_db, 999, update_data)
            
            assert result is None
            mock_db.commit.assert_not_called()
    
    @patch('app.repositories.user_repository.get_password_hash')
    def test_update_user_password(self, mock_hash):
        """Testa atualização de senha do usuário"""
        mock_hash.return_value = "new_hashed_password"
        mock_db = Mock()
        mock_user = User(
            id=1,
            email="user@example.com",
            username="user",
            hashed_password="old_hash",
            is_active=True,
            role=UserRole.USER
        )
        
        with patch.object(UserRepository, 'get_by_id', return_value=mock_user):
            update_data = UserUpdate(password="NewPassword123!")
            
            result = UserRepository.update(mock_db, 1, update_data)
            
            mock_hash.assert_called_once_with("NewPassword123!")
            mock_db.commit.assert_called_once()


class TestUserRepositoryDeleteMethod:
    """Testes para método DELETE do repositório"""
    
    def test_delete_user_success(self):
        """Testa exclusão de usuário com sucesso"""
        mock_db = Mock()
        mock_user = User(
            id=1,
            email="delete@example.com",
            username="deleteuser",
            hashed_password="hash",
            is_active=True,
            role=UserRole.USER
        )
        
        with patch.object(UserRepository, 'get_by_id', return_value=mock_user):
            result = UserRepository.delete(mock_db, 1)
            
            assert result is True
            mock_db.delete.assert_called_once_with(mock_user)
            mock_db.commit.assert_called_once()
    
    def test_delete_user_not_found(self):
        """Testa exclusão de usuário não encontrado"""
        mock_db = Mock()
        
        with patch.object(UserRepository, 'get_by_id', return_value=None):
            result = UserRepository.delete(mock_db, 999)
            
            assert result is False
            mock_db.delete.assert_not_called()
            mock_db.commit.assert_not_called()

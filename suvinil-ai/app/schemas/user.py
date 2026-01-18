"""Schemas de Usuário"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    """Schema base de usuário"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """Schema para criação de usuário"""
    password: str


class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """Schema de usuário no banco"""
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """Schema de resposta de usuário"""
    pass


class UserLogin(BaseModel):
    """Schema para login"""
    username: str
    password: str


class Token(BaseModel):
    """Schema de token JWT"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema de dados do token"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None

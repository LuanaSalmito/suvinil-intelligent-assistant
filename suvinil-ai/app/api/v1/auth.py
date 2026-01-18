"""
Endpoints de Autenticação

Este módulo fornece:
- Registro de novos usuários
- Login com JWT (suporta JSON e OAuth2 form-data)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserLogin, UserCreate, User, Token

router = APIRouter()


def _authenticate_user(db: Session, username: str, password: str):
    """Autentica usuário e retorna token"""
    user = UserRepository.get_by_username(db, username)
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value},
        expires_delta=access_token_expires,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/register",
    response_model=User,
    summary="Registrar novo usuário",
    description="Cria um novo usuário no sistema."
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Endpoint de registro de usuário"""
    # Verificar se username já existe
    if UserRepository.get_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username já está em uso",
        )
    
    # Verificar se email já existe
    if UserRepository.get_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso",
        )
    
    # Criar usuário
    user = UserRepository.create(db, user_data)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login (OAuth2 form-data)",
    description="""
Endpoint de login compatível com OAuth2.

**Formato**: application/x-www-form-urlencoded

**Campos**:
- username: nome de usuário
- password: senha

**Usuários de teste**:
- admin / admin123 (administrador)
- user / user123 (usuário comum)
- demo / demo123 (demonstração)
    """
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Endpoint de login com OAuth2 form-data"""
    return _authenticate_user(db, form_data.username, form_data.password)


@router.post(
    "/token",
    response_model=Token,
    summary="Login (JSON)",
    description="Endpoint de login com corpo JSON. Alternativa ao /login."
)
async def login_json(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """Endpoint de login com JSON body"""
    return _authenticate_user(db, credentials.username, credentials.password)

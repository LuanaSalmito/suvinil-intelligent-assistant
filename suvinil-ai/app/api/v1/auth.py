"""Endpoints de autenticação"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserLogin, Token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Endpoint de autenticação/login
    
    - Retorna JWT token para uso em requisições autenticadas
    - Token contém informações do usuário (id, username, role)
    - Token expira após o tempo configurado em ACCESS_TOKEN_EXPIRE_MINUTES
    
    **Roles disponíveis:**
    - `admin`: Acesso completo (chat + gerenciamento de catálogo)
    - `user`: Acesso ao chat
    
    **Exemplo de uso:**
    1. Faça login com username e password
    2. Use o token retornado no header: `Authorization: Bearer <token>`
    """
    user = UserRepository.get_by_username(db, credentials.username)
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
            "email": user.email,
        },
        expires_delta=access_token_expires,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

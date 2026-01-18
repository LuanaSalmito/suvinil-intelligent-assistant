"""Endpoints de usuários"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter()


@router.get("/me", response_model=User)
async def get_me(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Obtém usuário atual"""
    user = UserRepository.get_by_id(db, current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Lista todos os usuários (apenas admin)"""
    users = UserRepository.get_all(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Obtém usuário por ID"""
    # Usuários podem ver apenas seu próprio perfil, exceto admin
    if current_user["role"] != UserRole.ADMIN and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Cria novo usuário (apenas admin)"""
    # Verifica se username já existe
    if UserRepository.get_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Verifica se email já existe
    if UserRepository.get_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = UserRepository.create(db, user_data)
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Atualiza usuário"""
    # Usuários podem atualizar apenas seu próprio perfil, exceto admin
    if current_user["role"] != UserRole.ADMIN and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Não permite mudar role (apenas admin pode)
    if current_user["role"] != UserRole.ADMIN and user_data.role:
        user_data.role = None
    
    user = UserRepository.update(db, user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Deleta usuário (apenas admin)"""
    success = UserRepository.delete(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

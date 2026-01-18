"""Dependencies do FastAPI"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.models.user import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """Obtém usuário atual a partir do token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = UserRepository.get_by_username(db, username)
    if user is None:
        raise credentials_exception
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


async def get_current_active_user(
    current_user: Optional[dict] = Depends(get_current_user),
) -> Optional[dict]:
    """Obtém usuário ativo atual (opcional)"""
    if current_user is None:
        return None
    if not current_user.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_authenticated_user(
    current_user: Optional[dict] = Depends(get_current_active_user),
) -> dict:
    """Dependency que requer usuário autenticado e ativo"""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Factory para criar dependency que requer role específica (requer autenticação)"""
    async def role_checker(
        current_user: dict = Depends(require_authenticated_user)
    ) -> dict:
        user_role = current_user.get("role")
        
        # Se role é string, converter para enum
        if isinstance(user_role, str):
            try:
                user_role = UserRole(user_role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid user role",
                )
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker

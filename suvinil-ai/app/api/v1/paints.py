"""Endpoints de tintas"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role, require_authenticated_user
from app.models.user import UserRole
from app.models.paint import Environment, FinishType, PaintLine
from app.repositories.paint_repository import PaintRepository
from app.schemas.paint import Paint, PaintCreate, PaintUpdate

router = APIRouter()


@router.get("/", response_model=List[Paint])
async def list_paints(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    environment: Optional[Environment] = None,
    finish_type: Optional[FinishType] = None,
    line: Optional[PaintLine] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Lista tintas com filtros opcionais
    
    - Acesso público (não requer autenticação)
    - Todos podem visualizar o catálogo
    """
    paints = PaintRepository.get_all(
        db,
        skip=skip,
        limit=limit,
        environment=environment,
        finish_type=finish_type,
        line=line,
        search=search,
    )
    return paints


@router.get("/{paint_id}", response_model=Paint)
async def get_paint(
    paint_id: int,
    db: Session = Depends(get_db),
):
    """Obtém tinta por ID"""
    paint = PaintRepository.get_by_id(db, paint_id)
    if not paint or not paint.is_active:
        raise HTTPException(status_code=404, detail="Paint not found")
    return paint


@router.post("/", response_model=Paint, status_code=status.HTTP_201_CREATED)
async def create_paint(
    paint_data: PaintCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """
    Cria nova tinta no catálogo
    
    - Requer autenticação
    - Apenas usuários com role ADMIN podem criar tintas
    """
    paint = PaintRepository.create(db, paint_data, created_by=current_user["id"])
    return paint


@router.put("/{paint_id}", response_model=Paint)
async def update_paint(
    paint_id: int,
    paint_data: PaintUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """
    Atualiza tinta existente no catálogo
    
    - Requer autenticação
    - Apenas usuários com role ADMIN podem atualizar tintas
    """
    paint = PaintRepository.update(db, paint_id, paint_data)
    if not paint:
        raise HTTPException(status_code=404, detail="Paint not found")
    return paint


@router.delete("/{paint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_paint(
    paint_id: int,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """
    Deleta tinta do catálogo
    
    - Requer autenticação
    - Apenas usuários com role ADMIN podem deletar tintas
    """
    success = PaintRepository.delete(db, paint_id)
    if not success:
        raise HTTPException(status_code=404, detail="Paint not found")

"""Endpoints de tintas"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import UserRole
from app.models.paint import Ambiente, Acabamento, Linha
from app.repositories.paint_repository import PaintRepository
from app.schemas.paint import Paint, PaintCreate, PaintUpdate, PaintCount

router = APIRouter()


@router.get("/", response_model=List[Paint])
async def list_paints(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ambiente: Optional[Ambiente] = None,
    acabamento: Optional[Acabamento] = None,
    linha: Optional[Linha] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista tintas com filtros opcionais"""
    paints = PaintRepository.get_all(
        db,
        skip=skip,
        limit=limit,
        ambiente=ambiente,
        acabamento=acabamento,
        linha=linha,
        search=search,
    )
    return paints


@router.get("/count", response_model=PaintCount)
async def count_paints(
    ambiente: Optional[Ambiente] = None,
    acabamento: Optional[Acabamento] = None,
    linha: Optional[Linha] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Conta tintas ativas com filtros opcionais"""
    total = PaintRepository.count_active(
        db,
        ambiente=ambiente,
        acabamento=acabamento,
        linha=linha,
        search=search,
    )
    return PaintCount(total=total)


@router.get("/{paint_id}", response_model=Paint)
async def get_paint(
    paint_id: int,
    db: Session = Depends(get_db),
):
    """Obtém tinta por ID"""
    paint = PaintRepository.get_by_id(db, paint_id)
    if not paint or not paint.is_active:
        raise HTTPException(status_code=404, detail="Tinta não encontrada")
    return paint


@router.post("/", response_model=Paint, status_code=status.HTTP_201_CREATED)
async def create_paint(
    paint_data: PaintCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Cria nova tinta (apenas admin)"""
    paint = PaintRepository.create(db, paint_data.model_dump(), created_by=current_user["id"])
    return paint


@router.put("/{paint_id}", response_model=Paint)
async def update_paint(
    paint_id: int,
    paint_data: PaintUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Atualiza tinta (apenas admin)"""
    paint = PaintRepository.update(db, paint_id, paint_data.model_dump(exclude_unset=True))
    if not paint:
        raise HTTPException(status_code=404, detail="Tinta não encontrada")
    return paint


@router.delete("/{paint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_paint(
    paint_id: int,
    current_user: dict = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Deleta tinta (apenas admin)"""
    success = PaintRepository.delete(db, paint_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tinta não encontrada")

"""Repository de Tintas"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from app.models.paint import Paint, Environment, FinishType, PaintLine
from app.schemas.paint import PaintCreate, PaintUpdate


class PaintRepository:
    """Repository para operações de tinta"""
    
    @staticmethod
    def get_by_id(db: Session, paint_id: int) -> Optional[Paint]:
        """Busca tinta por ID"""
        return db.query(Paint).filter(Paint.id == paint_id).first()
    
    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        environment: Optional[Environment] = None,
        finish_type: Optional[FinishType] = None,
        line: Optional[PaintLine] = None,
        search: Optional[str] = None,
    ) -> List[Paint]:
        """Lista tintas com filtros"""
        query = db.query(Paint).filter(Paint.is_active == True)
        
        if environment:
            query = query.filter(Paint.environment == environment)
        
        if finish_type:
            query = query.filter(Paint.finish_type == finish_type)
        
        if line:
            query = query.filter(Paint.line == line)
        
        if search:
            search_filter = or_(
                Paint.name.ilike(f"%{search}%"),
                Paint.color_name.ilike(f"%{search}%"),
                Paint.surface_type.ilike(f"%{search}%"),
                Paint.features.ilike(f"%{search}%"),
                Paint.description.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, paint_data: PaintCreate, created_by: Optional[int] = None) -> Paint:
        """Cria nova tinta"""
        db_paint = Paint(
            **paint_data.model_dump(),
            created_by=created_by,
        )
        db.add(db_paint)
        db.commit()
        db.refresh(db_paint)
        return db_paint
    
    @staticmethod
    def update(db: Session, paint_id: int, paint_data: PaintUpdate) -> Optional[Paint]:
        """Atualiza tinta"""
        db_paint = PaintRepository.get_by_id(db, paint_id)
        if not db_paint:
            return None
        
        update_data = paint_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_paint, key, value)
        
        db.commit()
        db.refresh(db_paint)
        return db_paint
    
    @staticmethod
    def delete(db: Session, paint_id: int) -> bool:
        """Deleta tinta (soft delete)"""
        db_paint = PaintRepository.get_by_id(db, paint_id)
        if not db_paint:
            return False
        
        db_paint.is_active = False
        db.commit()
        return True

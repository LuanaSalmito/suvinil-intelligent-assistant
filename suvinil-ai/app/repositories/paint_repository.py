"""Repository para operações de banco de dados com Tintas"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.paint import Paint, Environment, FinishType, PaintLine


class PaintRepository:
    """Repository para gerenciar tintas no banco de dados"""
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Paint]:
        """Retorna todas as tintas ativas"""
        return db.query(Paint).filter(Paint.is_active == True).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, paint_id: int) -> Optional[Paint]:
        """Retorna tinta por ID"""
        return db.query(Paint).filter(Paint.id == paint_id, Paint.is_active == True).first()
    
    @staticmethod
    def search(
        db: Session,
        query: Optional[str] = None,
        environment: Optional[str] = None,
        finish_type: Optional[str] = None,
        color: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Paint]:
        """Busca tintas com filtros"""
        q = db.query(Paint).filter(Paint.is_active == True)
        
        if query:
            q = q.filter(
                or_(
                    Paint.name.ilike(f"%{query}%"),
                    Paint.description.ilike(f"%{query}%"),
                    Paint.features.ilike(f"%{query}%")
                )
            )
        
        if environment:
            q = q.filter(Paint.environment == environment)
        
        if finish_type:
            q = q.filter(Paint.finish_type == finish_type)
        
        if color:
            q = q.filter(
                or_(
                    Paint.color_name.ilike(f"%{color}%"),
                    Paint.color.ilike(f"%{color}%")
                )
            )
        
        return q.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_available_colors(db: Session) -> List[Dict[str, Any]]:
        """Retorna lista de cores disponíveis no catálogo com contagem"""
        colors = db.query(
            Paint.color_name,
            func.count(Paint.id).label('count')
        ).filter(
            Paint.is_active == True,
            Paint.color_name.isnot(None)
        ).group_by(
            Paint.color_name
        ).order_by(
            func.count(Paint.id).desc()
        ).all()
        
        return [
            {
                "color": color_name.lower() if color_name else "",
                "color_display": color_name,
                "count": count
            }
            for color_name, count in colors if color_name
        ]
    
    @staticmethod
    def find_by_color(
        db: Session,
        color: str,
        environment: Optional[str] = None,
        finish_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Paint]:
        """Busca tintas por cor específica"""
        q = db.query(Paint).filter(
            Paint.is_active == True,
            or_(
                Paint.color_name.ilike(f"%{color}%"),
                Paint.color.ilike(f"%{color}%")
            )
        )
        
        if environment:
            q = q.filter(Paint.environment == environment)
        
        if finish_type:
            q = q.filter(Paint.finish_type == finish_type)
        
        return q.limit(limit).all()
    
    @staticmethod
    def create(db: Session, paint_data: dict, created_by: Optional[int] = None) -> Paint:
        """Cria nova tinta"""
        paint = Paint(**paint_data, created_by=created_by)
        db.add(paint)
        db.commit()
        db.refresh(paint)
        return paint
    
    @staticmethod
    def update(db: Session, paint_id: int, paint_data: dict) -> Optional[Paint]:
        """Atualiza tinta existente"""
        paint = db.query(Paint).filter(Paint.id == paint_id).first()
        if not paint:
            return None
        
        for key, value in paint_data.items():
            setattr(paint, key, value)
        
        db.commit()
        db.refresh(paint)
        return paint
    
    @staticmethod
    def delete(db: Session, paint_id: int) -> bool:
        """Soft delete - marca como inativa"""
        paint = db.query(Paint).filter(Paint.id == paint_id).first()
        if not paint:
            return False
        
        paint.is_active = False
        db.commit()
        return True

"""Repository para operações de banco de dados com Tintas"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.paint import Paint, Ambiente, Acabamento, Linha


class PaintRepository:
    """Repository para gerenciar tintas no banco de dados"""

    @staticmethod
    def _normalize_text(value: Optional[str]) -> str:
        return (value or "").strip().lower()

    @staticmethod
    def _parse_environment_filter(environment: Optional[str]) -> Optional[List[Ambiente]]:
        """
        Converte texto de ambiente (ex.: "interno") em lista de enums aceitos.
        - "interno" inclui Interno e Interno/Externo
        - "externo" inclui Externo e Interno/Externo
        """
        env = PaintRepository._normalize_text(environment)
        if not env:
            return None
        if "intern" in env:
            return [Ambiente.INTERNO, Ambiente.INTERNO_EXTERNO]
        if any(k in env for k in ["extern", "fachada", "muro", "varanda"]):
            return [Ambiente.EXTERNO, Ambiente.INTERNO_EXTERNO]
        return None

    @staticmethod
    def _parse_finish(acabamento: Optional[str]) -> Optional[Acabamento]:
        a = PaintRepository._normalize_text(acabamento)
        if not a:
            return None
        if "fosc" in a:
            return Acabamento.FOSCO
        if "acet" in a or "semi" in a:
            return Acabamento.ACETINADO
        if "brilh" in a or "gloss" in a:
            return Acabamento.BRILHANTE
        return None

    @staticmethod
    def _surface_keywords(surface_type: Optional[str]) -> List[str]:
        s = PaintRepository._normalize_text(surface_type)
        if not s:
            return []
        # Normalização de sinônimos comuns
        if any(k in s for k in ["ferro", "metal", "aço", "aco", "alum", "inox"]):
            return ["metal", "ferro", "aço", "aco", "alum", "inox"]
        if any(k in s for k in ["madeira", "mdf", "compens", "laminad"]):
            return ["madeira", "mdf", "compens", "laminad"]
        if any(k in s for k in ["parede", "alvenaria", "reboco", "gesso", "massa", "cimento"]):
            return ["parede", "alvenaria", "reboco", "gesso", "massa", "cimento"]
        return [s]

    @staticmethod
    def recommend_candidates(
        db: Session,
        environment: Optional[str] = None,
        surface_type: Optional[str] = None,
        color: Optional[str] = None,
        finish_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Paint]:
        """
        Busca estruturada no catálogo para recomendação:
        - ambiente: interno/externo (inclui Interno/Externo)
        - superfície: substring + sinônimos (madeira/metal/parede)
        - cor: substring (ex.: "azul" casa com "azul claro")
        - acabamento: fosco/acetinado/brilhante
        """
        q = db.query(Paint).filter(Paint.is_active == True)

        env_list = PaintRepository._parse_environment_filter(environment)
        if env_list:
            q = q.filter(Paint.ambiente.in_(env_list))

        finish_enum = PaintRepository._parse_finish(finish_type)
        if finish_enum:
            q = q.filter(Paint.acabamento == finish_enum)

        cor = PaintRepository._normalize_text(color)
        if cor:
            q = q.filter(Paint.cor.ilike(f"%{cor}%"))

        surface_terms = PaintRepository._surface_keywords(surface_type)
        if surface_terms:
            surface_ors = [Paint.tipo_parede.ilike(f"%{term}%") for term in surface_terms]
            q = q.filter(or_(*surface_ors))

        return q.limit(limit).all()
    
    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        ambiente: Optional[Ambiente] = None,
        acabamento: Optional[Acabamento] = None,
        linha: Optional[Linha] = None,
        search: Optional[str] = None
    ) -> List[Paint]:
        """Retorna todas as tintas ativas com filtros opcionais"""
        query = db.query(Paint).filter(Paint.is_active == True)
        
        if ambiente:
            query = query.filter(Paint.ambiente == ambiente)
        
        if acabamento:
            query = query.filter(Paint.acabamento == acabamento)
        
        if linha:
            query = query.filter(Paint.linha == linha)
        
        if search:
            query = query.filter(
                or_(
                    Paint.nome.ilike(f"%{search}%"),
                    Paint.cor.ilike(f"%{search}%"),
                    Paint.features.ilike(f"%{search}%")
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, paint_id: int) -> Optional[Paint]:
        """Retorna tinta por ID"""
        return db.query(Paint).filter(Paint.id == paint_id, Paint.is_active == True).first()
    
    @staticmethod
    def count_active(
        db: Session,
        ambiente: Optional[Ambiente] = None,
        acabamento: Optional[Acabamento] = None,
        linha: Optional[Linha] = None,
        search: Optional[str] = None
    ) -> int:
        """Conta tintas ativas com filtros opcionais"""
        query = db.query(func.count(Paint.id)).filter(Paint.is_active == True)
        
        if ambiente:
            query = query.filter(Paint.ambiente == ambiente)
        
        if acabamento:
            query = query.filter(Paint.acabamento == acabamento)
        
        if linha:
            query = query.filter(Paint.linha == linha)
        
        if search:
            query = query.filter(
                or_(
                    Paint.nome.ilike(f"%{search}%"),
                    Paint.cor.ilike(f"%{search}%"),
                    Paint.features.ilike(f"%{search}%")
                )
            )
        
        return query.scalar()
    
    @staticmethod
    def search(
        db: Session,
        query: Optional[str] = None,
        ambiente: Optional[str] = None,
        acabamento: Optional[str] = None,
        cor: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Paint]:
        """Busca tintas com filtros"""
        q = db.query(Paint).filter(Paint.is_active == True)
        
        if query:
            q = q.filter(
                or_(
                    Paint.nome.ilike(f"%{query}%"),
                    Paint.cor.ilike(f"%{query}%"),
                    Paint.features.ilike(f"%{query}%")
                )
            )
        
        if ambiente:
            env_list = PaintRepository._parse_environment_filter(ambiente)
            if env_list:
                q = q.filter(Paint.ambiente.in_(env_list))
        
        if acabamento:
            finish_enum = PaintRepository._parse_finish(acabamento)
            if finish_enum:
                q = q.filter(Paint.acabamento == finish_enum)
        
        if cor:
            q = q.filter(Paint.cor.ilike(f"%{cor}%"))
        
        return q.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_available_colors(db: Session) -> List[Dict[str, Any]]:
        """Retorna lista de cores disponíveis no catálogo com contagem"""
        colors = db.query(
            Paint.cor,
            func.count(Paint.id).label('count')
        ).filter(
            Paint.is_active == True,
            Paint.cor.isnot(None)
        ).group_by(
            Paint.cor
        ).order_by(
            func.count(Paint.id).desc()
        ).all()
        
        return [
            {
                "cor": cor.lower() if cor else "",
                "cor_display": cor,
                "count": count
            }
            for cor, count in colors if cor
        ]
    
    @staticmethod
    def find_by_color(
        db: Session,
        cor: str,
        ambiente: Optional[str] = None,
        acabamento: Optional[str] = None,
        limit: int = 10
    ) -> List[Paint]:
        """Busca tintas por cor específica"""
        q = db.query(Paint).filter(
            Paint.is_active == True,
            Paint.cor.ilike(f"%{cor}%")
        )
        
        if ambiente:
            q = q.filter(Paint.ambiente == ambiente)
        
        if acabamento:
            q = q.filter(Paint.acabamento == acabamento)
        
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

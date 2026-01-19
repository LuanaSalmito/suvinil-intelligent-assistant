from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.paint import Paint
from app.models.paint import Environment


class RagService:

    def search_paints(
        self,
        db: Session,
        filters: Dict
    ) -> List[Paint]:

        query = db.query(Paint).filter(Paint.is_active == True)

        if filters.get("environment"):
            query = query.filter(Paint.environment == Environment(filters["environment"]))

        if filters.get("surface_type"):
            query = query.filter(
                Paint.surface_type.ilike(f"%{filters['surface_type']}%")
            )

        if filters.get("feature"):
            query = query.filter(
                Paint.features.ilike(f"%{filters['feature']}%")
            )

        if filters.get("finish_type"):
            query = query.filter(Paint.finish_type == filters["finish_type"])

        return query.limit(5).all()

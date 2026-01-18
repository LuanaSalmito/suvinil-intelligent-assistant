"""Schemas de Tinta"""
from pydantic import BaseModel
from typing import Optional
from app.models.paint import Environment, FinishType, PaintLine


class PaintBase(BaseModel):
    name: str
    color: Optional[str] = None
    color_name: Optional[str] = None
    surface_type: Optional[str] = None
    environment: Environment
    finish_type: FinishType
    features: Optional[str] = None
    line: PaintLine
    price: Optional[float] = None
    description: Optional[str] = None


class PaintCreate(PaintBase):
    pass


class PaintUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    color_name: Optional[str] = None
    surface_type: Optional[str] = None
    environment: Optional[Environment] = None
    finish_type: Optional[FinishType] = None
    features: Optional[str] = None
    line: Optional[PaintLine] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PaintInDB(PaintBase):
    id: int
    is_active: bool
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True


class Paint(PaintInDB):
   
    pass

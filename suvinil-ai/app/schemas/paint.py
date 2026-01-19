"""Schemas de Tinta"""
from pydantic import BaseModel
from typing import Optional
from app.models.paint import Ambiente, Acabamento, Linha


class PaintBase(BaseModel):
    """Schema base de tinta"""
    nome: str
    cor: Optional[str] = None
    tipo_parede: Optional[str] = None
    ambiente: Ambiente
    acabamento: Acabamento
    features: Optional[str] = None
    linha: Linha


class PaintCreate(PaintBase):
    """Schema para criação de tinta"""
    pass


class PaintUpdate(BaseModel):
    """Schema para atualização de tinta"""
    nome: Optional[str] = None
    cor: Optional[str] = None
    tipo_parede: Optional[str] = None
    ambiente: Optional[Ambiente] = None
    acabamento: Optional[Acabamento] = None
    features: Optional[str] = None
    linha: Optional[Linha] = None
    is_active: Optional[bool] = None


class PaintInDB(PaintBase):
    """Schema de tinta no banco"""
    id: int
    is_active: bool
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True


class Paint(PaintInDB):
    """Schema de resposta de tinta"""
    pass


class PaintCount(BaseModel):
    """Schema para contagem de tintas"""
    total: int

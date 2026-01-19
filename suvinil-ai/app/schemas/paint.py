"""Schemas de Tinta"""
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
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


class Paint(BaseModel):
    """Schema de resposta de tinta"""
    id: int
    nome: str
    cor: Optional[str] = None
    tipo_parede: Optional[str] = None
    ambiente: Ambiente
    acabamento: Acabamento
    features: List[str] = []
    aplicacao: List[str] = []
    linha: Linha
    is_active: bool
    created_by: Optional[int] = None
    
    @field_validator('features', mode='before')
    @classmethod
    def parse_features(cls, v):
        """Converte features de string para lista"""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [f.strip() for f in v.split(',') if f.strip()]
        return []
    
    @model_validator(mode='after')
    def populate_aplicacao(self):
        """Popula aplicacao baseado no tipo_parede"""
        if not self.aplicacao or len(self.aplicacao) == 0:
            if self.tipo_parede:
                self.aplicacao = [t.strip() for t in self.tipo_parede.split(',') if t.strip()]
        return self
    
    class Config:
        from_attributes = True


class PaintCount(BaseModel):
    """Schema para contagem de tintas"""
    total: int

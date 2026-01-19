"""Modelo de Tinta"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class Ambiente(str, enum.Enum):
    """Ambiente de aplicação"""
    INTERNO = "Interno"
    EXTERNO = "Externo"
    INTERNO_EXTERNO = "Interno/Externo"


class Acabamento(str, enum.Enum):
    """Tipo de acabamento"""
    FOSCO = "Fosco"
    ACETINADO = "Acetinado"
    BRILHANTE = "Brilhante"


class Linha(str, enum.Enum):
    """Linha do produto"""
    PREMIUM = "Premium"
    STANDARD = "Standard"


class Paint(Base):
    """Modelo de Tinta - baseado na planilha Base_de_Dados_de_Tintas_Suvinil.xlsx"""
    __tablename__ = "paints"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    cor = Column(String, nullable=True)
    tipo_parede = Column(String, nullable=True)
    ambiente = Column(Enum(Ambiente), nullable=False, default=Ambiente.INTERNO)
    acabamento = Column(Enum(Acabamento), nullable=False, default=Acabamento.FOSCO)
    features = Column(Text, nullable=True)
    linha = Column(Enum(Linha), nullable=False, default=Linha.STANDARD)
    is_active = Column(Boolean, default=True)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="paints")


Environment = Ambiente
FinishType = Acabamento
PaintLine = Linha

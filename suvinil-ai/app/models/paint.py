
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class Environment(str, enum.Enum):
   
    INTERIOR = "interno"
    EXTERIOR = "externo"
    BOTH = "ambos"


class FinishType(str, enum.Enum):
    FOSCO = "fosco"
    ACETINADO = "acetinado"
    BRILHANTE = "brilhante"
    SEMI_BRILHANTE = "semi-brilhante"


class PaintLine(str, enum.Enum):
    PREMIUM = "Premium"
    STANDARD = "Standard"
    ECONOMY = "Economy"


class Paint(Base):
    __tablename__ = "paints"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    color = Column(String, nullable=True) 
    color_name = Column(String, nullable=True) 
    surface_type = Column(String, nullable=True)  
    environment = Column(Enum(Environment), nullable=False, default=Environment.INTERIOR)
    finish_type = Column(Enum(FinishType), nullable=False, default=FinishType.FOSCO)
    features = Column(Text, nullable=True) 
    line = Column(Enum(PaintLine), nullable=False, default=PaintLine.STANDARD)
    price = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
   
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="paints")

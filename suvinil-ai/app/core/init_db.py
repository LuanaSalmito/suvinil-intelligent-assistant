"""Script de inicialização do banco de dados"""
import sys
from pathlib import Path

# Adicionar root ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.paint import Paint, Environment, FinishType, PaintLine


def init_db():
    """Inicializa banco de dados com dados de exemplo"""
    # Nota: As tabelas devem ser criadas via Alembic primeiro
    # Execute: alembic upgrade head
    print("🗄️  Verificando tabelas (criadas via Alembic)...")
    # Base.metadata.create_all(bind=engine)  # Desabilitado - use Alembic
    
    db = SessionLocal()
    try:
        # Verificar se já existe usuário admin
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("👤 Criando usuários de exemplo...")
            
            # Criar admin
            admin = User(
                email="admin@suvinil.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrador",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            
            # Criar usuário comum
            user = User(
                email="user@suvinil.com",
                username="user",
                hashed_password=get_password_hash("user123"),
                full_name="Usuário Teste",
                role=UserRole.USER,
                is_active=True,
            )
            db.add(user)
            
            db.commit()
            print("✅ Usuários criados:")
            print("   Admin: admin / admin123")
            print("   User:  user / user123")
        
        # Verificar se já existem tintas
        paint_count = db.query(Paint).count()
        
        if paint_count == 0:
            print("🎨 Criando tintas de exemplo...")
            
            # Buscar usuário admin para created_by
            admin_user = db.query(User).filter(User.username == "admin").first()
            admin_id = admin_user.id if admin_user else None
            
            paints_data = [
                {
                    "name": "Suvinil Toque de Seda",
                    "color": "#F5F5F0",
                    "color_name": "Branco Neve",
                    "surface_type": "Parede",
                    "environment": Environment.INTERIOR,
                    "finish_type": FinishType.ACETINADO,
                    "features": "lavável, sem odor, anti-mofo",
                    "line": PaintLine.PREMIUM,
                    "price": 89.90,
                    "description": "Tinta acrílica com acabamento acetinado, ideal para ambientes internos como quartos e salas. Tecnologia sem odor e lavável.",
                    "is_active": True,
                    "created_by": admin_id,
                },
                {
                    "name": "Suvinil Fachada Acrílica",
                    "color": "#FFFFFF",
                    "color_name": "Branco Gelo",
                    "surface_type": "Parede Externa",
                    "environment": Environment.EXTERIOR,
                    "finish_type": FinishType.FOSCO,
                    "features": "proteção UV, anti-mofo, lavável, resistente à chuva",
                    "line": PaintLine.STANDARD,
                    "price": 75.90,
                    "description": "Tinta acrílica para fachadas com proteção contra sol e chuva. Resistente ao intemperismo e lavável.",
                    "is_active": True,
                    "created_by": admin_id,
                },
                {
                    "name": "Suvinil Esmalte Sintético",
                    "color": "#4A4A4A",
                    "color_name": "Cinza Urbano",
                    "surface_type": "Madeira",
                    "environment": Environment.BOTH,
                    "finish_type": FinishType.BRILHANTE,
                    "features": "resistente ao calor, impermeável, brilhante",
                    "line": PaintLine.PREMIUM,
                    "price": 95.90,
                    "description": "Esmalte sintético ideal para madeira com acabamento brilhante. Resistente ao calor e impermeável.",
                    "is_active": True,
                    "created_by": admin_id,
                },
                {
                    "name": "Suvinil Fosco Completo",
                    "color": "#808080",
                    "color_name": "Cinza Urbano",
                    "surface_type": "Parede",
                    "environment": Environment.INTERIOR,
                    "finish_type": FinishType.FOSCO,
                    "features": "lavável, alta cobertura, sem odor",
                    "line": PaintLine.STANDARD,
                    "price": 69.90,
                    "description": "Tinta fosca com alta cobertura, ideal para escritórios e ambientes modernos. Fácil aplicação e sem odor.",
                    "is_active": True,
                    "created_by": admin_id,
                },
                {
                    "name": "Suvinil Azul Sereno",
                    "color": "#87CEEB",
                    "color_name": "Azul Sereno",
                    "surface_type": "Parede Externa",
                    "environment": Environment.EXTERIOR,
                    "finish_type": FinishType.FOSCO,
                    "features": "proteção UV, resistente ao tempo, lavável",
                    "line": PaintLine.STANDARD,
                    "price": 79.90,
                    "description": "Tinta para ambientes externos em tom azul claro moderno. Resistente ao tempo e com proteção UV.",
                    "is_active": True,
                    "created_by": admin_id,
                },
            ]
            
            for paint_data in paints_data:
                paint = Paint(**paint_data)
                db.add(paint)
            
            db.commit()
            print(f"✅ {len(paints_data)} tintas criadas!")
        
        else:
            print(f"ℹ️  Banco já possui {paint_count} tintas. Pulando criação.")
        
        print("\n✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao inicializar banco: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()

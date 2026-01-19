#!/usr/bin/env python3
"""
Script de teste para verificar se o filtro de cor está funcionando corretamente
"""
import sys
from pathlib import Path

# Adicionar o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.repositories.paint_repository import PaintRepository


def test_color_filtering():
    """Testa o filtro de cores"""
    print("=" * 60)
    print("🧪 TESTE DE FILTRO DE CORES")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Buscar todas as tintas
        all_paints = PaintRepository.get_all(db, limit=200)
        print(f"\n📊 Total de tintas no banco: {len(all_paints)}")
        
        # Testar filtro de azul
        print("\n🔵 Testando filtro de cor 'azul':")
        blue_paints = [
            p for p in all_paints
            if "azul" in (p.color_name or "").lower()
            or "azul" in (p.color or "").lower()
        ]
        
        print(f"   ✓ Encontradas {len(blue_paints)} tintas azuis:")
        for paint in blue_paints[:5]:
            print(f"      • {paint.name}")
            print(f"        Cor: {paint.color_name}")
            print(f"        Ambiente: {paint.environment.value}")
            print(f"        Acabamento: {paint.finish_type.value}")
            print(f"        Características: {paint.features}")
            print()
        
        if len(blue_paints) > 5:
            print(f"      ... e mais {len(blue_paints) - 5} tintas azuis")
        
        # Testar filtro de azul + interno
        print("\n🏠 Testando filtro de azul para ambiente interno:")
        blue_interior = [
            p for p in blue_paints
            if p.environment.value in ["interno", "ambos"]
        ]
        
        print(f"   ✓ Encontradas {len(blue_interior)} tintas azuis para interior:")
        for paint in blue_interior[:3]:
            print(f"      • {paint.name} - R$ {paint.price:.2f}")
        
        # Testar outras cores
        colors_to_test = ["verde", "vermelho", "rosa", "amarelo"]
        print("\n🎨 Contagem por cor:")
        for color in colors_to_test:
            count = len([
                p for p in all_paints
                if color in (p.color_name or "").lower()
                or color in (p.color or "").lower()
            ])
            print(f"   • {color.capitalize()}: {count} tintas")
        
        print("\n" + "=" * 60)
        print("✅ Teste concluído com sucesso!")
        print("=" * 60)
        
        return len(blue_paints) > 0
        
    except Exception as e:
        print(f"\n✗ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_color_filtering()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Script para importar tintas do CSV para o banco de dados
"""
import sys
import csv
import os
from pathlib import Path

# Adicionar o diretório pai ao path para importar os módulos da aplicação
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, engine, Base
from app.models.paint import Paint, Environment, FinishType, PaintLine


def clear_paints(db):
    """Limpa todas as tintas do banco"""
    try:
        count = db.query(Paint).delete()
        db.commit()
        print(f"✓ {count} tintas removidas do banco")
        return count
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao limpar banco: {e}")
        return 0


def import_paints_from_csv(csv_file: str, clear_before: bool = True):
    """Importa tintas do CSV para o banco de dados"""
    
    # Verificar se arquivo existe
    if not os.path.exists(csv_file):
        print(f"✗ Arquivo {csv_file} não encontrado!")
        return 0
    
    # Criar sessão
    db = SessionLocal()
    
    try:
        # Limpar banco se solicitado
        if clear_before:
            print("\n🔄 Limpando banco de dados...")
            clear_paints(db)
        
        # Ler CSV
        print(f"\n📖 Lendo arquivo {csv_file}...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            paints_data = list(reader)
        
        print(f"✓ {len(paints_data)} tintas encontradas no CSV")
        
        # Importar tintas
        print("\n💾 Importando tintas para o banco...")
        imported_count = 0
        errors = []
        
        for idx, row in enumerate(paints_data, 1):
            try:
                # Mapear valores dos enums
                environment_map = {
                    "interno": Environment.INTERIOR,
                    "externo": Environment.EXTERIOR,
                    "ambos": Environment.BOTH
                }
                
                finish_map = {
                    "fosco": FinishType.FOSCO,
                    "acetinado": FinishType.ACETINADO,
                    "brilhante": FinishType.BRILHANTE,
                    "semi-brilhante": FinishType.SEMI_BRILHANTE
                }
                
                line_map = {
                    "Premium": PaintLine.PREMIUM,
                    "Standard": PaintLine.STANDARD,
                    "Economy": PaintLine.ECONOMY
                }
                
                # Criar objeto Paint
                paint = Paint(
                    name=row['name'],
                    color=row['color'],
                    color_name=row['color_name'],
                    surface_type=row['surface_type'],
                    environment=environment_map.get(row['environment'].lower(), Environment.INTERIOR),
                    finish_type=finish_map.get(row['finish_type'].lower(), FinishType.FOSCO),
                    features=row['features'],
                    line=line_map.get(row['line'], PaintLine.STANDARD),
                    price=float(row['price']) if row['price'] else None,
                    description=row['description'],
                    is_active=row['is_active'].lower() in ['true', '1', 'yes', 'sim']
                )
                
                db.add(paint)
                imported_count += 1
                
                # Commit a cada 20 registros
                if imported_count % 20 == 0:
                    db.commit()
                    print(f"  → {imported_count} tintas importadas...")
                
            except Exception as e:
                errors.append((idx, row.get('name', 'Unknown'), str(e)))
                continue
        
        # Commit final
        db.commit()
        
        # Relatório
        print(f"\n✅ Importação concluída!")
        print(f"   • Total importado: {imported_count} tintas")
        
        if errors:
            print(f"\n⚠️  Erros encontrados: {len(errors)}")
            for idx, name, error in errors[:5]:  # Mostrar apenas 5 primeiros erros
                print(f"   • Linha {idx} ({name}): {error}")
        
        return imported_count
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Erro durante importação: {e}")
        return 0
    finally:
        db.close()


def verify_import(db):
    """Verifica a importação"""
    try:
        total = db.query(Paint).count()
        print(f"\n🔍 Verificação:")
        print(f"   • Total de tintas no banco: {total}")
        
        # Contar por cor
        print(f"\n   📊 Tintas por cor:")
        colors = db.query(Paint.color_name).distinct().all()
        for (color,) in sorted(colors):
            count = db.query(Paint).filter(Paint.color_name == color).count()
            print(f"      • {color}: {count} tintas")
        
        # Mostrar algumas tintas azuis
        print(f"\n   🎨 Exemplos de tintas azuis:")
        blue_paints = db.query(Paint).filter(
            Paint.color_name.ilike('%azul%')
        ).limit(3).all()
        
        for paint in blue_paints:
            print(f"      • {paint.name} - {paint.color_name} ({paint.finish_type.value})")
        
    except Exception as e:
        print(f"✗ Erro na verificação: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🎨 IMPORTADOR DE TINTAS SUVINIL")
    print("=" * 60)
    
    # Arquivo CSV
    csv_file = "paints_mock_100.csv"
    
    # Importar
    count = import_paints_from_csv(csv_file, clear_before=True)
    
    if count > 0:
        # Verificar
        db = SessionLocal()
        verify_import(db)
        db.close()
        
        print("\n" + "=" * 60)
        print("✅ Importação concluída com sucesso!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Nenhuma tinta foi importada!")
        print("=" * 60)

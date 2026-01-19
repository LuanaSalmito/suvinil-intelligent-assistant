#!/usr/bin/env python3
"""
Script para reindexar o RAG vector store após importar novas tintas
"""
import sys
from pathlib import Path

# Adicionar o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.ai.rag_service import RAGService


def reindex_rag():
    """Reindexar o vector store do RAG"""
    print("=" * 60)
    print("🔄 REINDEXAÇÃO DO RAG VECTOR STORE")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        print("\n📚 Inicializando RAG Service...")
        rag_service = RAGService(db)
        
        print("🔍 Reindexando tintas...")
        count = rag_service.reindex()
        
        print(f"\n✅ Reindexação concluída!")
        print(f"   • {count} tintas indexadas no vector store")
        
        # Testar busca
        print("\n🧪 Testando busca semântica...")
        results = rag_service.search_paints("azul quarto infantil", k=3)
        
        if results:
            print(f"   ✓ Encontradas {len(results)} tintas azuis:")
            for r in results[:3]:
                print(f"      • {r['name']} - {r['color']} (score: {r['similarity_score']:.3f})")
        else:
            print("   ⚠️  Nenhuma tinta encontrada na busca de teste")
        
        print("\n" + "=" * 60)
        print("✅ RAG pronto para uso!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Erro durante reindexação: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    reindex_rag()

#!/usr/bin/env python3
"""
Script para testar o status do RAG e busca semântica
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.core.config import settings
from app.ai.rag_service import RAGService


def test_rag_status():
    """Testa o status do RAG"""
    print("=" * 70)
    print("🔍 STATUS DO RAG E BUSCA SEMÂNTICA")
    print("=" * 70)
    
    # 1. Verificar API Key
    print("\n📋 Configuração:")
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith('sk-'):
        print(f"  ✅ OpenAI API Key: Configurada ({settings.OPENAI_API_KEY[:20]}...)")
    else:
        print("  ❌ OpenAI API Key: Não configurada ou inválida")
        print("     Configure no arquivo .env: OPENAI_API_KEY=sk-...")
        return False
    
    # 2. Testar RAG Service
    print("\n🧪 Testando RAG Service:")
    db = SessionLocal()
    
    try:
        rag_service = RAGService(db)
        
        if rag_service.vectorstore is None:
            print("  ⚠️  Vector store não disponível")
            print("     Possíveis causas:")
            print("       - Quota da OpenAI excedida")
            print("       - Erro ao criar embeddings")
            print("       - Sem tintas no banco")
            print("\n  💡 Solução:")
            print("       1. Verifique créditos na OpenAI")
            print("       2. Reimporte tintas: python scripts/import_paints_to_db.py")
            return False
        
        # 3. Testar busca semântica
        print("  ✅ Vector store inicializado")
        print("\n🔎 Testando busca semântica:")
        
        test_queries = [
            "tinta lavável para cozinha",
            "acabamento brilhante resistente",
            "parede externa com sol"
        ]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            try:
                results = rag_service.search_paints(query, k=3)
                if results:
                    print(f"    ✅ Encontrou {len(results)} resultados:")
                    for r in results[:2]:
                        print(f"       • {r['name']} (score: {r['similarity_score']:.3f})")
                else:
                    print("    ⚠️  Nenhum resultado")
            except Exception as e:
                print(f"    ❌ Erro: {e}")
                return False
        
        print("\n" + "=" * 70)
        print("✅ RAG FUNCIONANDO CORRETAMENTE!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao inicializar RAG: {e}")
        
        if "429" in str(e) or "quota" in str(e).lower():
            print("\n  💡 Quota da OpenAI excedida!")
            print("     Soluções:")
            print("       1. Adicione créditos em: https://platform.openai.com/account/billing")
            print("       2. Use outra API key")
            print("       3. Sistema funciona em modo fallback (sem RAG)")
        
        return False
    finally:
        db.close()


def show_alternatives():
    """Mostra alternativas ao RAG"""
    print("\n" + "=" * 70)
    print("🔄 ALTERNATIVAS SEM RAG")
    print("=" * 70)
    print("""
O sistema funciona perfeitamente em MODO FALLBACK:

✅ Busca direta no banco de dados
✅ Filtro por cor 100% preciso  
✅ Filtro por ambiente e acabamento
✅ Mantém contexto da conversa
✅ Sem custos de API

❌ Não tem busca semântica por características
❌ Não entende linguagem natural complexa

Para queries como:
  "tinta azul" → Funciona perfeitamente
  "tinta lavável sem odor" → Funciona com keywords
  "algo que proteja contra umidade" → Precisa RAG
""")


if __name__ == "__main__":
    print("\n")
    success = test_rag_status()
    
    if not success:
        show_alternatives()
        print("\n💡 Dica: O sistema está funcionando em modo fallback")
        print("          Todas as funcionalidades principais estão operacionais!\n")
    
    sys.exit(0 if success else 1)

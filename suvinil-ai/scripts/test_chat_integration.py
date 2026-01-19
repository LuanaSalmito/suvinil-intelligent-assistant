#!/usr/bin/env python3
"""
Script de teste completo para verificar se o sistema de chat está
identificando cores corretamente e fazendo recomendações adequadas.
"""
import sys
from pathlib import Path

# Adicionar o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.repositories.paint_repository import PaintRepository
from app.api.v1.ai_chat import _simple_chat_response


def print_section(title: str):
    """Imprime seção formatada"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_color_detection():
    """Testa a detecção de cores no chat"""
    print_section("🧪 TESTE 1: Detecção de Cores")
    
    db = SessionLocal()
    
    test_cases = [
        "quero pintar o quarto do meu filho de azul",
        "eu queria uma cor vibrante azul",
        "tem tinta verde para sala?",
        "preciso de vermelho",
        "quais cores vocês tem?",
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n[Teste {i}] Mensagem: \"{message}\"")
        print("-" * 70)
        
        try:
            response = _simple_chat_response(message, db, user_id=999)
            print(f"Resposta: {response['response']}")
            print(f"Tintas mencionadas: {response['paints_mentioned']}")
            print(f"Modo: {response['metadata']['mode']}")
            
            # Verificar se a cor foi respeitada
            if "azul" in message.lower() and "azul" not in response['response'].lower():
                print("⚠️  ATENÇÃO: Cor azul solicitada mas não aparece na resposta!")
            elif "verde" in message.lower() and "verde" not in response['response'].lower():
                print("⚠️  ATENÇÃO: Cor verde solicitada mas não aparece na resposta!")
            elif "vermelho" in message.lower() and "vermelho" not in response['response'].lower():
                print("⚠️  ATENÇÃO: Cor vermelho solicitada mas não aparece na resposta!")
            else:
                print("✅ Resposta coerente com a cor solicitada")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()


def test_available_colors():
    """Testa listagem de cores disponíveis"""
    print_section("🎨 TESTE 2: Cores Disponíveis no Banco")
    
    db = SessionLocal()
    
    try:
        colors = PaintRepository.get_available_colors(db)
        print(f"Total de cores no catálogo: {len(colors)}\n")
        
        for color_info in colors:
            print(f"  • {color_info['color_display']:<15} → {color_info['count']:>2} tintas")
        
        # Verificar se tem cores principais
        colors_dict = {c['color'].lower(): c['count'] for c in colors}
        
        essential_colors = ['azul', 'verde', 'vermelho', 'branco']
        print("\n" + "-" * 70)
        print("Verificação de cores essenciais:")
        for color in essential_colors:
            if color in colors_dict:
                print(f"  ✅ {color.capitalize()}: {colors_dict[color]} tintas")
            else:
                print(f"  ❌ {color.capitalize()}: Não encontrado!")
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_color_search():
    """Testa busca por cor específica"""
    print_section("🔍 TESTE 3: Busca por Cor Específica")
    
    db = SessionLocal()
    
    colors_to_test = ['azul', 'verde', 'vermelho', 'rosa']
    
    for color in colors_to_test:
        print(f"\n[Buscando] Cor: {color}")
        print("-" * 70)
        
        try:
            paints = PaintRepository.find_by_color(db, color=color, limit=3)
            
            if paints:
                print(f"✅ Encontradas {len(paints)} tintas {color}:")
                for paint in paints:
                    print(f"  • {paint.name}")
                    print(f"    Cor: {paint.color_name}")
                    print(f"    Ambiente: {paint.environment.value}")
                    print(f"    Preço: R$ {paint.price:.2f}")
                    print()
            else:
                print(f"⚠️  Nenhuma tinta {color} encontrada")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    db.close()


def test_context_memory():
    """Testa memória de contexto"""
    print_section("🧠 TESTE 4: Memória de Contexto")
    
    db = SessionLocal()
    user_id = 1000
    
    conversation = [
        "quero pintar o quarto do meu filho de 5 anos",
        "eu queria azul",
    ]
    
    print("Simulando conversa sequencial:\n")
    
    for i, message in enumerate(conversation, 1):
        print(f"[{i}] Usuário: {message}")
        
        try:
            response = _simple_chat_response(message, db, user_id=user_id)
            print(f"[{i}] IA: {response['response'][:200]}...")
            print()
            
            if i == 2:  # Segunda mensagem deve lembrar do contexto
                if "quarto" in response['response'].lower() or "filho" in response['response'].lower():
                    print("✅ Sistema manteve contexto da conversa anterior")
                else:
                    print("⚠️  Sistema pode ter perdido contexto")
                    
                if "azul" in response['response'].lower():
                    print("✅ Cor azul foi identificada e aplicada")
                else:
                    print("❌ Cor azul não aparece na resposta!")
                    
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    db.close()


def main():
    """Executa todos os testes"""
    print("\n" + "=" * 70)
    print("  🎨 TESTE DE INTEGRAÇÃO - CHAT COM IDENTIFICAÇÃO DE CORES")
    print("=" * 70)
    
    try:
        test_available_colors()
        test_color_search()
        test_color_detection()
        test_context_memory()
        
        print("\n" + "=" * 70)
        print("  ✅ TESTES CONCLUÍDOS!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro geral nos testes: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

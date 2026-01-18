
from openai import OpenAI
from app.core.config import settings


def example_openai_usage():
 
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY
    )
    
   
    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": "Você é um assistente especialista em tintas."},
            {"role": "user", "content": "write a haiku about ai"}
        ],
        temperature=0.7,
    )
    
    print("Resposta do Chat:")
    print(response.choices[0].message.content)
    print()
    
   
    simple_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "write a haiku about ai"}
        ],
    )
    
    print("Resposta simples:")
    print(simple_response.choices[0].message.content)
    print()
    
   
    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",
        input="Tinta para quarto, lavável e sem odor"
    )
    
    print("Embedding gerado:")
    print(f"Dimensão: {len(embedding_response.data[0].embedding)}")
    print(f"Primeiros 5 valores: {embedding_response.data[0].embedding[:5]}")
    print()
    
    # Exemplo 4: Geração de imagens com DALL·E (opcional - feature extra)
    # Descomente para testar geração de imagens
    # image_response = client.images.generate(
    #     model="dall-e-3",
    #     prompt="Uma sala moderna pintada com tinta cinza claro",
    #     size="1024x1024",
    #     quality="standard",
    #     n=1,
    # )
    # print("URL da imagem:", image_response.data[0].url)


if __name__ == "__main__":
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        print("❌ Erro: OPENAI_API_KEY não configurada no .env")
        print("   Configure a chave no arquivo .env antes de executar este exemplo.")
    else:
        print("🚀 Testando conexão com OpenAI...")
        print()
        try:
            example_openai_usage()
            print("✅ Teste concluído com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao conectar com OpenAI: {e}")
            print("   Verifique se sua API key está correta e tem créditos disponíveis.")

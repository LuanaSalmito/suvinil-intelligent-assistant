"""
Gerador de Visualizações com IA (DALL-E)

Gera imagens simulando a aplicação de tintas em ambientes,
permitindo ao usuário visualizar como ficaria a cor escolhida.
"""

import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Gerador de imagens usando DALL-E da OpenAI
    """
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada")
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("ImageGenerator inicializado com DALL-E")
    
    def _build_prompt(
        self,
        color: str,
        environment: str,
        finish: str = "fosco"
    ) -> str:
        """
        Constrói prompt otimizado para DALL-E
        """
        
        # Mapeamento de cores para descrições visuais
        color_descriptions = {
            "azul": "blue paint, calming azure tone",
            "vermelho": "red paint, vibrant crimson tone",
            "verde": "green paint, fresh sage tone",
            "amarelo": "yellow paint, warm sunny tone",
            "branco": "white paint, pure clean tone",
            "cinza": "gray paint, modern neutral tone",
            "rosa": "pink paint, soft pastel tone",
            "roxo": "purple paint, elegant lavender tone",
            "laranja": "orange paint, energetic tangerine tone",
            "bege": "beige paint, warm neutral tone",
        }
        
        color_desc = color_descriptions.get(color.lower(), f"{color} paint")
        
        # Mapeamento de acabamentos
        finish_descriptions = {
            "fosco": "matte finish, elegant and modern",
            "brilhante": "glossy finish, vibrant and reflective",
            "acetinado": "satin finish, subtle sheen",
            "semi-brilhante": "semi-gloss finish, balanced appearance"
        }
        
        finish_desc = finish_descriptions.get(finish.lower(), "matte finish")
        
        # Prompt otimizado para DALL-E
        prompt = f"""A modern and well-lit {environment}, professionally painted with {color_desc} in {finish_desc}.
The room features clean walls with the paint freshly applied, showing excellent coverage.
Natural lighting highlights the color beautifully.
Professional interior design photography, high quality, realistic, 8k.
The paint color is the main focus, showing how it transforms the space."""
        
        return prompt
    
    async def generate_paint_visualization(
        self,
        color: str,
        environment: str = "living room",
        finish: str = "fosco",
        size: str = "1024x1024"
    ) -> str:
        """
        Gera visualização da tinta aplicada em um ambiente
        
        Args:
            color: Cor da tinta (azul, verde, vermelho, etc.)
            environment: Tipo de ambiente (quarto, sala, fachada, etc.)
            finish: Tipo de acabamento (fosco, brilhante, acetinado)
            size: Tamanho da imagem (1024x1024, 1792x1024, 1024x1792)
        
        Returns:
            URL da imagem gerada
        """
        
        logger.info(f"Gerando visualização: cor={color}, ambiente={environment}, acabamento={finish}")
        
        # Mapear ambiente para descrição em inglês
        environment_map = {
            "quarto": "bedroom",
            "sala": "living room",
            "escritório": "office",
            "banheiro": "bathroom",
            "cozinha": "kitchen",
            "fachada": "house exterior facade",
            "muro": "exterior wall",
            "varanda": "balcony",
        }
        
        env_desc = environment_map.get(environment.lower(), environment)
        
        try:
            # Construir prompt
            prompt = self._build_prompt(color, env_desc, finish)
            
            logger.info(f"Prompt DALL-E: {prompt[:100]}...")
            
            # Gerar imagem com DALL-E 3
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            logger.info(f"Imagem gerada com sucesso: {image_url[:50]}...")
            
            return image_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar imagem: {e}")
            raise
    
    async def generate_comparison(
        self,
        color1: str,
        color2: str,
        environment: str = "living room"
    ) -> tuple[str, str]:
        """
        Gera duas imagens para comparação de cores
        
        Returns:
            Tupla com URLs das duas imagens
        """
        
        logger.info(f"Gerando comparação: {color1} vs {color2} em {environment}")
        
        try:
            # Gerar ambas as imagens em paralelo seria mais eficiente,
            # mas por simplicidade faremos sequencial
            image1 = await self.generate_paint_visualization(color1, environment)
            image2 = await self.generate_paint_visualization(color2, environment)
            
            return (image1, image2)
            
        except Exception as e:
            logger.error(f"Erro ao gerar comparação: {e}")
            raise


async def generate_paint_visualization_simple(
    color: str,
    environment: str = "sala",
    finish: str = "fosco"
) -> Optional[str]:
    """
    Função auxiliar para gerar visualização de forma simples
    """
    try:
        generator = ImageGenerator()
        return await generator.generate_paint_visualization(color, environment, finish)
    except Exception as e:
        logger.error(f"Erro ao gerar visualização: {e}")
        return None

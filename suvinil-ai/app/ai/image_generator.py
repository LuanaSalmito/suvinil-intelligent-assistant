"""
Gerador de Visualizações com IA (DALL-E)

Gera imagens simulando a aplicação de tintas em ambientes,
permitindo ao usuário visualizar como ficaria a cor escolhida.
"""

import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.ai.prompts import prompt_manager

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Gerador de imagens usando DALL-E da OpenAI
    """
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada")
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.prompts = prompt_manager.get_image_prompts()
        self.color_descriptions = self.prompts.get('color_descriptions', {})
        self.finish_descriptions = self.prompts.get('finish_descriptions', {})
        self.environment_map = self.prompts.get('environment_map', {})
        self.dalle_prompt_template = self.prompts.get('dalle_prompt_template', '')
        
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
        default_color = self.color_descriptions.get('default', '{color} paint')
        color_desc = self.color_descriptions.get(color.lower(), default_color.format(color=color))
        
        default_finish = self.finish_descriptions.get('default', 'matte finish')
        finish_desc = self.finish_descriptions.get(finish.lower(), default_finish)
        
        prompt = self.dalle_prompt_template.format(
            environment=environment,
            color_desc=color_desc,
            finish_desc=finish_desc
        )
        
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
        
        env_desc = self.environment_map.get(environment.lower(), environment)
        
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

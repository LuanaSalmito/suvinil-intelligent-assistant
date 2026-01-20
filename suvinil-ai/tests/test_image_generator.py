"""Testes para o módulo de geração de imagens (ImageGenerator)"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.ai.image_generator import ImageGenerator, generate_paint_visualization_simple


class TestImageGenerator:
    """Testes para a classe ImageGenerator"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Fixture para resposta mockada da API OpenAI"""
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].url = "https://example.com/generated-image.png"
        return mock_response
    
    @pytest.fixture
    def mock_settings(self):
        """Fixture para configurações mockadas"""
        with patch('app.ai.image_generator.settings') as mock:
            mock.OPENAI_API_KEY = "test-api-key-12345"
            yield mock
    
    @pytest.fixture
    def mock_prompt_manager(self):
        """Fixture para prompt manager mockado"""
        with patch('app.ai.image_generator.prompt_manager') as mock:
            mock.get_image_prompts.return_value = {
                'color_descriptions': {
                    'azul': 'vibrant azure blue',
                    'verde': 'fresh forest green',
                    'vermelho': 'bold crimson red',
                    'default': '{color} paint'
                },
                'finish_descriptions': {
                    'fosco': 'matte finish',
                    'brilhante': 'glossy finish',
                    'acetinado': 'satin finish',
                    'default': 'matte finish'
                },
                'environment_map': {
                    'sala': 'living room',
                    'quarto': 'bedroom',
                    'cozinha': 'kitchen',
                    'fachada': 'exterior facade'
                },
                'dalle_prompt_template': 'A photorealistic {environment} with walls painted in {color_desc} with {finish_desc}'
            }
            yield mock
    
    def test_initialization_success(self, mock_settings, mock_prompt_manager):
        """Teste: Inicialização bem-sucedida do ImageGenerator"""
        generator = ImageGenerator()
        
        assert generator.client is not None
        assert generator.color_descriptions is not None
        assert generator.finish_descriptions is not None
        assert generator.environment_map is not None
        assert generator.dalle_prompt_template is not None
    
    def test_initialization_without_api_key(self, mock_prompt_manager):
        """Teste: Inicialização falha sem API key"""
        with patch('app.ai.image_generator.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            
            with pytest.raises(ValueError, match="OPENAI_API_KEY não configurada"):
                ImageGenerator()
    
    def test_build_prompt_with_default_color(self, mock_settings, mock_prompt_manager):
        """Teste: Construção de prompt com cor padrão (não mapeada)"""
        generator = ImageGenerator()
        
        prompt = generator._build_prompt(
            color="roxo",  # Cor não está no mapa
            environment="sala",
            finish="fosco"
        )
        
        assert "roxo" in prompt.lower() or "purple" in prompt.lower()
        assert "living room" in prompt.lower() or "sala" in prompt.lower()
        assert "matte" in prompt.lower() or "fosco" in prompt.lower()
    
    def test_build_prompt_with_mapped_color(self, mock_settings, mock_prompt_manager):
        """Teste: Construção de prompt com cor mapeada"""
        generator = ImageGenerator()
        
        prompt = generator._build_prompt(
            color="azul",
            environment="quarto",
            finish="acetinado"
        )
        
        assert "azure" in prompt.lower() or "azul" in prompt.lower()
        assert "bedroom" in prompt.lower() or "quarto" in prompt.lower()
        assert "satin" in prompt.lower() or "acetinado" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_generate_paint_visualization_success(
        self, 
        mock_settings, 
        mock_prompt_manager, 
        mock_openai_response
    ):
        """Teste: Geração de visualização bem-sucedida"""
        generator = ImageGenerator()
        
        # Mock da chamada à API do OpenAI
        generator.client.images.generate = AsyncMock(return_value=mock_openai_response)
        
        image_url = await generator.generate_paint_visualization(
            color="azul",
            environment="sala",
            finish="fosco",
            size="1024x1024"
        )
        
        assert image_url == "https://example.com/generated-image.png"
        generator.client.images.generate.assert_called_once()
        
        # Verifica os parâmetros passados
        call_args = generator.client.images.generate.call_args
        assert call_args.kwargs['model'] == "dall-e-3"
        assert call_args.kwargs['size'] == "1024x1024"
        assert call_args.kwargs['quality'] == "standard"
        assert call_args.kwargs['n'] == 1
    
    @pytest.mark.asyncio
    async def test_generate_paint_visualization_with_different_sizes(
        self, 
        mock_settings, 
        mock_prompt_manager, 
        mock_openai_response
    ):
        """Teste: Geração com diferentes tamanhos de imagem"""
        generator = ImageGenerator()
        generator.client.images.generate = AsyncMock(return_value=mock_openai_response)
        
        # Testa diferentes tamanhos
        sizes = ["1024x1024", "1792x1024", "1024x1792"]
        
        for size in sizes:
            image_url = await generator.generate_paint_visualization(
                color="verde",
                environment="cozinha",
                finish="brilhante",
                size=size
            )
            
            assert image_url == "https://example.com/generated-image.png"
            call_args = generator.client.images.generate.call_args
            assert call_args.kwargs['size'] == size
    
    @pytest.mark.asyncio
    async def test_generate_paint_visualization_api_error(
        self, 
        mock_settings, 
        mock_prompt_manager
    ):
        """Teste: Tratamento de erro da API OpenAI"""
        generator = ImageGenerator()
        
        # Simula erro na API
        generator.client.images.generate = AsyncMock(
            side_effect=Exception("API Error: Rate limit exceeded")
        )
        
        with pytest.raises(Exception, match="API Error"):
            await generator.generate_paint_visualization(
                color="vermelho",
                environment="fachada",
                finish="fosco"
            )
    
    @pytest.mark.asyncio
    async def test_generate_comparison_success(
        self, 
        mock_settings, 
        mock_prompt_manager, 
        mock_openai_response
    ):
        """Teste: Geração de comparação entre duas cores"""
        generator = ImageGenerator()
        generator.client.images.generate = AsyncMock(return_value=mock_openai_response)
        
        image1_url, image2_url = await generator.generate_comparison(
            color1="azul",
            color2="verde",
            environment="sala"
        )
        
        assert image1_url == "https://example.com/generated-image.png"
        assert image2_url == "https://example.com/generated-image.png"
        assert generator.client.images.generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_comparison_first_image_fails(
        self, 
        mock_settings, 
        mock_prompt_manager
    ):
        """Teste: Comparação falha se primeira imagem der erro"""
        generator = ImageGenerator()
        
        # Simula erro na primeira chamada
        generator.client.images.generate = AsyncMock(
            side_effect=Exception("First image generation failed")
        )
        
        with pytest.raises(Exception, match="First image generation failed"):
            await generator.generate_comparison(
                color1="azul",
                color2="verde",
                environment="quarto"
            )
    
    @pytest.mark.asyncio
    async def test_generate_paint_visualization_simple_success(
        self, 
        mock_settings, 
        mock_prompt_manager, 
        mock_openai_response
    ):
        """Teste: Função auxiliar generate_paint_visualization_simple"""
        with patch('app.ai.image_generator.ImageGenerator') as MockGenerator:
            mock_instance = MockGenerator.return_value
            mock_instance.generate_paint_visualization = AsyncMock(
                return_value="https://example.com/simple-image.png"
            )
            
            result = await generate_paint_visualization_simple(
                color="azul",
                environment="sala",
                finish="fosco"
            )
            
            assert result == "https://example.com/simple-image.png"
            mock_instance.generate_paint_visualization.assert_called_once_with(
                "azul", "sala", "fosco"
            )
    
    @pytest.mark.asyncio
    async def test_generate_paint_visualization_simple_error(self, mock_settings, mock_prompt_manager):
        """Teste: Função auxiliar retorna None em caso de erro"""
        with patch('app.ai.image_generator.ImageGenerator') as MockGenerator:
            mock_instance = MockGenerator.return_value
            mock_instance.generate_paint_visualization = AsyncMock(
                side_effect=Exception("API Error")
            )
            
            result = await generate_paint_visualization_simple(
                color="vermelho",
                environment="fachada"
            )
            
            assert result is None
    
    def test_build_prompt_all_parameters(self, mock_settings, mock_prompt_manager):
        """Teste: Construção de prompt com todos os parâmetros"""
        generator = ImageGenerator()
        
        prompt = generator._build_prompt(
            color="verde",
            environment="cozinha",
            finish="brilhante"
        )
        
        # Verifica que o prompt foi construído
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        
        # Verifica elementos do template
        assert "kitchen" in prompt.lower() or "cozinha" in prompt.lower()

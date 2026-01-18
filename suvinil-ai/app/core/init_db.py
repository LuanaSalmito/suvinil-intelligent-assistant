"""
Script de inicialização do banco de dados.

Cria:
- Usuários de exemplo (admin e user)
- Catálogo completo de tintas Suvinil (enriquecido)
"""
import sys
from pathlib import Path

# Adicionar root ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.paint import Paint, Environment, FinishType, PaintLine


# ============================================================================
# CATÁLOGO DE TINTAS SUVINIL
# ============================================================================
# Catálogo enriquecido com diversas opções para diferentes necessidades

TINTAS_CATALOGO = [
    # ========================================
    # LINHA PREMIUM - INTERIORES
    # ========================================
    {
        "name": "Suvinil Toque de Seda",
        "color": "#F5F5F0",
        "color_name": "Branco Neve",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "lavável, sem odor, anti-mofo, alta cobertura",
        "line": PaintLine.PREMIUM,
        "price": 189.90,
        "description": "Tinta acrílica premium com acabamento acetinado, ideal para ambientes internos como quartos e salas. Tecnologia sem odor permite pintar sem sair de casa. Alta lavabilidade e resistência a manchas.",
    },
    {
        "name": "Suvinil Toque de Seda",
        "color": "#F5E6D3",
        "color_name": "Pérola",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "lavável, sem odor, anti-mofo, alta cobertura",
        "line": PaintLine.PREMIUM,
        "price": 189.90,
        "description": "Tom sofisticado de pérola com acabamento acetinado. Ideal para quartos e salas de estar que buscam elegância e aconchego.",
    },
    {
        "name": "Suvinil Toque de Seda",
        "color": "#C4B7A6",
        "color_name": "Camurça",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "lavável, sem odor, anti-mofo, alta cobertura",
        "line": PaintLine.PREMIUM,
        "price": 189.90,
        "description": "Tom terroso e acolhedor, perfeito para criar ambientes aconchegantes. Acabamento acetinado facilita a limpeza.",
    },
    {
        "name": "Suvinil Ilumina",
        "color": "#FFFEF5",
        "color_name": "Branco Luminoso",
        "surface_type": "Parede, Teto",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "alta luminosidade, sem odor, anti-mofo, teto e parede",
        "line": PaintLine.PREMIUM,
        "price": 169.90,
        "description": "Tinta especial com pigmentos que maximizam a reflexão de luz, tornando ambientes mais claros e amplos. Ideal para corredores, tetos e espaços pequenos.",
    },
    {
        "name": "Suvinil Criativa",
        "color": "#FF6B6B",
        "color_name": "Coral Vibrante",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "lavável, alta pigmentação, sem odor, cores intensas",
        "line": PaintLine.PREMIUM,
        "price": 199.90,
        "description": "Linha de cores vibrantes e intensas para quem quer ousar na decoração. Alta pigmentação garante cobertura uniforme mesmo em tons fortes.",
    },
    {
        "name": "Suvinil Criativa",
        "color": "#4ECDC4",
        "color_name": "Turquesa Tropical",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "lavável, alta pigmentação, sem odor, cores intensas",
        "line": PaintLine.PREMIUM,
        "price": 199.90,
        "description": "Tom vibrante que traz energia e frescor ao ambiente. Perfeito para espaços que precisam de um toque de cor e personalidade.",
    },
    {
        "name": "Suvinil Acrílico Fosco Premium",
        "color": "#2C3E50",
        "color_name": "Azul Petróleo",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "lavável, sem odor, alta cobertura, elegante",
        "line": PaintLine.PREMIUM,
        "price": 179.90,
        "description": "Tom sofisticado de azul petróleo para quem busca elegância e modernidade. Acabamento fosco proporciona visual contemporâneo.",
    },
    
    # ========================================
    # LINHA PREMIUM - EXTERIORES
    # ========================================
    {
        "name": "Suvinil Fachada Premium",
        "color": "#FFFFFF",
        "color_name": "Branco Gelo",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "proteção UV, anti-mofo, lavável, resistente à chuva, 15 anos de garantia",
        "line": PaintLine.PREMIUM,
        "price": 199.90,
        "description": "Tinta premium para fachadas com máxima proteção contra intempéries. Tecnologia anti-algas e anti-mofo, com garantia de 15 anos contra descascamento.",
    },
    {
        "name": "Suvinil Fachada Premium",
        "color": "#F5DEB3",
        "color_name": "Areia",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "proteção UV, anti-mofo, lavável, resistente à chuva, 15 anos de garantia",
        "line": PaintLine.PREMIUM,
        "price": 199.90,
        "description": "Tom clássico de areia para fachadas elegantes. Resistente ao sol intenso e chuvas frequentes.",
    },
    {
        "name": "Suvinil Sol & Chuva",
        "color": "#D2691E",
        "color_name": "Terracota",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "proteção UV extrema, impermeável, anti-mofo, alta durabilidade",
        "line": PaintLine.PREMIUM,
        "price": 219.90,
        "description": "Linha de máxima resistência para regiões com clima severo. Proteção UV extrema e impermeabilização que resiste às condições mais adversas.",
    },
    {
        "name": "Suvinil Sol & Chuva",
        "color": "#8B4513",
        "color_name": "Marrom Colonial",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "proteção UV extrema, impermeável, anti-mofo, alta durabilidade",
        "line": PaintLine.PREMIUM,
        "price": 219.90,
        "description": "Tom clássico colonial com máxima proteção. Ideal para casas em estilo rústico ou colonial.",
    },
    
    # ========================================
    # LINHA STANDARD - INTERIORES
    # ========================================
    {
        "name": "Suvinil Fosco Completo",
        "color": "#808080",
        "color_name": "Cinza Urbano",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "lavável, alta cobertura, sem odor, fácil aplicação",
        "line": PaintLine.STANDARD,
        "price": 129.90,
        "description": "Tinta fosca com alta cobertura, ideal para escritórios e ambientes modernos. Acabamento fosco disfarça imperfeições da parede.",
    },
    {
        "name": "Suvinil Fosco Completo",
        "color": "#F5F5DC",
        "color_name": "Bege Clássico",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "lavável, alta cobertura, sem odor, fácil aplicação",
        "line": PaintLine.STANDARD,
        "price": 129.90,
        "description": "Tom versátil que combina com qualquer decoração. Alta cobertura e fácil aplicação.",
    },
    {
        "name": "Suvinil Fosco Completo",
        "color": "#FFFFF0",
        "color_name": "Gelo",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "lavável, alta cobertura, sem odor, fácil aplicação",
        "line": PaintLine.STANDARD,
        "price": 119.90,
        "description": "Branco gelo clássico para qualquer ambiente. Excelente custo-benefício com qualidade Suvinil.",
    },
    {
        "name": "Suvinil Acrílico Acetinado",
        "color": "#FFF8DC",
        "color_name": "Palha",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "lavável, sem odor, bom rendimento",
        "line": PaintLine.STANDARD,
        "price": 139.90,
        "description": "Acabamento acetinado suave que facilita a limpeza. Cor neutra que ilumina o ambiente.",
    },
    {
        "name": "Suvinil Clássica Liso",
        "color": "#98D8C8",
        "color_name": "Verde Água",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "sem odor, fácil aplicação, boa cobertura",
        "line": PaintLine.STANDARD,
        "price": 109.90,
        "description": "Tom refrescante que traz tranquilidade ao ambiente. Ideal para banheiros e lavabos.",
    },
    {
        "name": "Suvinil Clássica Liso",
        "color": "#FFE4E1",
        "color_name": "Rosa Bebê",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "sem odor, fácil aplicação, boa cobertura",
        "line": PaintLine.STANDARD,
        "price": 109.90,
        "description": "Tom delicado para quartos infantis. Sem odor para segurança dos pequenos.",
    },
    {
        "name": "Suvinil Clássica Liso",
        "color": "#ADD8E6",
        "color_name": "Azul Bebê",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "sem odor, fácil aplicação, boa cobertura",
        "line": PaintLine.STANDARD,
        "price": 109.90,
        "description": "Tom suave ideal para quartos de bebê. Formulação segura e sem odor.",
    },
    
    # ========================================
    # LINHA STANDARD - EXTERIORES
    # ========================================
    {
        "name": "Suvinil Fachada Acrílica",
        "color": "#FFFFFF",
        "color_name": "Branco Neve",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "proteção UV, anti-mofo, lavável, resistente à chuva, 7 anos de garantia",
        "line": PaintLine.STANDARD,
        "price": 139.90,
        "description": "Tinta acrílica para fachadas com excelente custo-benefício. Proteção contra sol e chuva com 7 anos de garantia.",
    },
    {
        "name": "Suvinil Fachada Acrílica",
        "color": "#87CEEB",
        "color_name": "Azul Sereno",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "proteção UV, anti-mofo, lavável, resistente à chuva",
        "line": PaintLine.STANDARD,
        "price": 139.90,
        "description": "Tom azul claro moderno para fachadas. Resistente ao tempo e fácil de limpar.",
    },
    {
        "name": "Suvinil Fachada Acrílica",
        "color": "#90EE90",
        "color_name": "Verde Primavera",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "proteção UV, anti-mofo, lavável, resistente à chuva",
        "line": PaintLine.STANDARD,
        "price": 139.90,
        "description": "Tom verde fresco para fachadas que se integram com a natureza. Boa resistência ao clima.",
    },
    {
        "name": "Suvinil Muro e Fachada",
        "color": "#A9A9A9",
        "color_name": "Cinza Médio",
        "surface_type": "Muro",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "resistente à chuva, anti-mofo, fácil aplicação, econômico",
        "line": PaintLine.STANDARD,
        "price": 99.90,
        "description": "Tinta econômica para muros e fachadas. Boa proteção com excelente custo-benefício.",
    },
    
    # ========================================
    # LINHA ECONOMY
    # ========================================
    {
        "name": "Suvinil Látex PVA",
        "color": "#FFFFFF",
        "color_name": "Branco",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "econômico, boa cobertura, fácil aplicação",
        "line": PaintLine.ECONOMY,
        "price": 69.90,
        "description": "Opção econômica para pintura interna. Boa cobertura e fácil aplicação para quem busca praticidade.",
    },
    {
        "name": "Suvinil Látex PVA",
        "color": "#F0F0F0",
        "color_name": "Gelo",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "econômico, boa cobertura, fácil aplicação",
        "line": PaintLine.ECONOMY,
        "price": 69.90,
        "description": "Tinta econômica em tom gelo suave. Ideal para renovar ambientes com baixo custo.",
    },
    {
        "name": "Suvinil Rende Muito",
        "color": "#FFFAFA",
        "color_name": "Branco Neve",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "alto rendimento, econômico, fácil aplicação",
        "line": PaintLine.ECONOMY,
        "price": 59.90,
        "description": "Máximo rendimento por litro, ideal para grandes áreas. Excelente opção para quem precisa economizar.",
    },
    {
        "name": "Suvinil Fachada Econômica",
        "color": "#FFFFFF",
        "color_name": "Branco",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "econômico, proteção básica, fácil aplicação",
        "line": PaintLine.ECONOMY,
        "price": 79.90,
        "description": "Opção econômica para fachadas. Proteção básica contra intempéries com bom custo-benefício.",
    },
    
    # ========================================
    # ESMALTES E TINTAS ESPECIAIS
    # ========================================
    {
        "name": "Suvinil Esmalte Sintético",
        "color": "#FFFFFF",
        "color_name": "Branco",
        "surface_type": "Madeira, Metal",
        "environment": Environment.BOTH,
        "finish_type": FinishType.BRILHANTE,
        "features": "resistente ao calor, impermeável, alta durabilidade, secagem rápida",
        "line": PaintLine.PREMIUM,
        "price": 159.90,
        "description": "Esmalte sintético premium para madeira e metal. Acabamento brilhante resistente ao calor e impermeável. Ideal para portas, janelas e móveis.",
    },
    {
        "name": "Suvinil Esmalte Sintético",
        "color": "#4A4A4A",
        "color_name": "Cinza Grafite",
        "surface_type": "Madeira, Metal",
        "environment": Environment.BOTH,
        "finish_type": FinishType.BRILHANTE,
        "features": "resistente ao calor, impermeável, alta durabilidade, secagem rápida",
        "line": PaintLine.PREMIUM,
        "price": 159.90,
        "description": "Esmalte em tom cinza grafite moderno. Perfeito para móveis e elementos decorativos contemporâneos.",
    },
    {
        "name": "Suvinil Esmalte Sintético",
        "color": "#000000",
        "color_name": "Preto",
        "surface_type": "Madeira, Metal",
        "environment": Environment.BOTH,
        "finish_type": FinishType.BRILHANTE,
        "features": "resistente ao calor, impermeável, alta durabilidade, secagem rápida",
        "line": PaintLine.PREMIUM,
        "price": 159.90,
        "description": "Preto intenso com acabamento brilhante. Ideal para grades, portões e elementos de destaque.",
    },
    {
        "name": "Suvinil Esmalte Água",
        "color": "#FFFFFF",
        "color_name": "Branco",
        "surface_type": "Madeira, Metal",
        "environment": Environment.BOTH,
        "finish_type": FinishType.ACETINADO,
        "features": "sem odor, secagem rápida, fácil limpeza, baixo VOC",
        "line": PaintLine.PREMIUM,
        "price": 169.90,
        "description": "Esmalte à base de água, sem odor forte. Ideal para móveis de quarto de bebê e ambientes que precisam de pintura sem interromper o uso.",
    },
    {
        "name": "Suvinil Esmalte Água",
        "color": "#F8F8FF",
        "color_name": "Branco Acetinado",
        "surface_type": "Madeira, Metal",
        "environment": Environment.BOTH,
        "finish_type": FinishType.SEMI_BRILHANTE,
        "features": "sem odor, secagem rápida, fácil limpeza, baixo VOC",
        "line": PaintLine.PREMIUM,
        "price": 169.90,
        "description": "Acabamento semi-brilhante elegante. Perfeito para móveis e portas que precisam de resistência e beleza.",
    },
    {
        "name": "Suvinil Verniz Marítimo",
        "color": "#CD853F",
        "color_name": "Natural Madeira",
        "surface_type": "Madeira",
        "environment": Environment.BOTH,
        "finish_type": FinishType.BRILHANTE,
        "features": "proteção UV, impermeável, resistente à maresia, alta durabilidade",
        "line": PaintLine.PREMIUM,
        "price": 179.90,
        "description": "Verniz de máxima proteção para madeira. Resistente à maresia e intempéries. Ideal para decks, pérgolas e móveis de jardim.",
    },
    {
        "name": "Suvinil Stain Impregnante",
        "color": "#8B4513",
        "color_name": "Imbuia",
        "surface_type": "Madeira",
        "environment": Environment.BOTH,
        "finish_type": FinishType.ACETINADO,
        "features": "proteção UV, penetração profunda, realça veios, anti-fungo",
        "line": PaintLine.STANDARD,
        "price": 149.90,
        "description": "Stain impregnante que penetra na madeira protegendo de dentro para fora. Realça a beleza natural dos veios.",
    },
    {
        "name": "Suvinil Stain Impregnante",
        "color": "#A0522D",
        "color_name": "Mogno",
        "surface_type": "Madeira",
        "environment": Environment.BOTH,
        "finish_type": FinishType.ACETINADO,
        "features": "proteção UV, penetração profunda, realça veios, anti-fungo",
        "line": PaintLine.STANDARD,
        "price": 149.90,
        "description": "Tom mogno sofisticado que valoriza móveis e estruturas de madeira. Proteção completa contra fungos e UV.",
    },
    
    # ========================================
    # TINTAS ESPECIAIS - TEXTURAS E EFEITOS
    # ========================================
    {
        "name": "Suvinil Textura Acrílica",
        "color": "#FFFFFF",
        "color_name": "Branco",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "textura rústica, impermeável, esconde imperfeições, anti-mofo",
        "line": PaintLine.STANDARD,
        "price": 119.90,
        "description": "Textura acrílica que esconde imperfeições da parede. Efeito rústico decorativo com proteção contra umidade.",
    },
    {
        "name": "Suvinil Textura Acrílica",
        "color": "#DEB887",
        "color_name": "Areia Natural",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "textura rústica, impermeável, esconde imperfeições, anti-mofo",
        "line": PaintLine.STANDARD,
        "price": 119.90,
        "description": "Textura em tom areia para fachadas com visual natural. Excelente para esconder defeitos da superfície.",
    },
    {
        "name": "Suvinil Grafiato",
        "color": "#C0C0C0",
        "color_name": "Cinza Claro",
        "surface_type": "Parede Externa",
        "environment": Environment.EXTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "textura grafiato, impermeável, decorativo, anti-mofo",
        "line": PaintLine.STANDARD,
        "price": 129.90,
        "description": "Textura tipo grafiato para fachadas modernas. Efeito decorativo durável e resistente às intempéries.",
    },
    {
        "name": "Suvinil Massa Corrida PVA",
        "color": "#FFFFFF",
        "color_name": "Branco",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "preparo de superfície, alta cobertura, fácil lixamento",
        "line": PaintLine.STANDARD,
        "price": 49.90,
        "description": "Massa corrida para preparo e nivelamento de paredes internas. Proporciona superfície lisa e uniforme para pintura.",
    },
    {
        "name": "Suvinil Selador Acrílico",
        "color": "#FFFFFF",
        "color_name": "Transparente",
        "surface_type": "Parede",
        "environment": Environment.BOTH,
        "finish_type": FinishType.FOSCO,
        "features": "preparo de superfície, reduz absorção, melhora rendimento",
        "line": PaintLine.STANDARD,
        "price": 89.90,
        "description": "Selador acrílico para preparo de superfícies. Reduz a absorção da parede e melhora o rendimento da tinta.",
    },
    
    # ========================================
    # LINHA ANTIMOFO E ANTIBACTÉRIA
    # ========================================
    {
        "name": "Suvinil Anti Mofo",
        "color": "#FFFFFF",
        "color_name": "Branco",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.FOSCO,
        "features": "anti-mofo reforçado, lavável, ideal para banheiros, resistente à umidade",
        "line": PaintLine.PREMIUM,
        "price": 189.90,
        "description": "Tinta com tecnologia anti-mofo reforçada, ideal para banheiros, lavanderias e áreas úmidas. Proteção prolongada contra fungos e bactérias.",
    },
    {
        "name": "Suvinil Antibactéria",
        "color": "#FFFFFF",
        "color_name": "Branco Hospitalar",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "antibactéria, lavável, ideal para hospitais, fácil higienização",
        "line": PaintLine.PREMIUM,
        "price": 229.90,
        "description": "Tinta com tecnologia antibactéria para ambientes que exigem máxima higiene. Ideal para hospitais, clínicas, cozinhas industriais e escolas.",
    },
    {
        "name": "Suvinil Antibactéria",
        "color": "#F0FFF0",
        "color_name": "Verde Hospital",
        "surface_type": "Parede",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.ACETINADO,
        "features": "antibactéria, lavável, ideal para hospitais, fácil higienização",
        "line": PaintLine.PREMIUM,
        "price": 229.90,
        "description": "Verde suave com proteção antibacteriana. Cor tradicional de ambientes hospitalares com máxima proteção.",
    },
    
    # ========================================
    # TINTAS PARA PISO
    # ========================================
    {
        "name": "Suvinil Piso Acrílico",
        "color": "#808080",
        "color_name": "Cinza",
        "surface_type": "Piso de Concreto",
        "environment": Environment.BOTH,
        "finish_type": FinishType.SEMI_BRILHANTE,
        "features": "resistente à abrasão, lavável, secagem rápida, antiderrapante",
        "line": PaintLine.STANDARD,
        "price": 169.90,
        "description": "Tinta acrílica para pisos de concreto. Resistente ao tráfego e fácil de limpar. Ideal para garagens, áreas de serviço e calçadas.",
    },
    {
        "name": "Suvinil Piso Acrílico",
        "color": "#8B0000",
        "color_name": "Vermelho Óxido",
        "surface_type": "Piso de Concreto",
        "environment": Environment.BOTH,
        "finish_type": FinishType.SEMI_BRILHANTE,
        "features": "resistente à abrasão, lavável, secagem rápida, antiderrapante",
        "line": PaintLine.STANDARD,
        "price": 169.90,
        "description": "Vermelho óxido clássico para pisos. Alta resistência ao desgaste e fácil manutenção.",
    },
    {
        "name": "Suvinil Piso Acrílico",
        "color": "#006400",
        "color_name": "Verde Colonial",
        "surface_type": "Piso de Concreto",
        "environment": Environment.BOTH,
        "finish_type": FinishType.SEMI_BRILHANTE,
        "features": "resistente à abrasão, lavável, secagem rápida, antiderrapante",
        "line": PaintLine.STANDARD,
        "price": 169.90,
        "description": "Verde colonial tradicional para pisos externos. Boa resistência e acabamento durável.",
    },
    {
        "name": "Suvinil Epóxi Base Água",
        "color": "#D3D3D3",
        "color_name": "Cinza Claro",
        "surface_type": "Piso de Concreto",
        "environment": Environment.INTERIOR,
        "finish_type": FinishType.SEMI_BRILHANTE,
        "features": "alta resistência, lavável, sem odor, industrial",
        "line": PaintLine.PREMIUM,
        "price": 249.90,
        "description": "Epóxi à base de água para pisos industriais. Alta resistência química e mecânica com aplicação sem odor forte.",
    },
]


def init_db():
    """Inicializa banco de dados com dados de exemplo"""
    print("=" * 60)
    print("   SUVINIL AI - Inicialização do Banco de Dados")
    print("=" * 60)
    
    print("\n[1/3] Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("      Tabelas criadas com sucesso!")
    
    db = SessionLocal()
    try:
        # ========================================
        # CRIAR USUÁRIOS
        # ========================================
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("\n[2/3] Criando usuários de exemplo...")
            
            # Criar admin
            admin = User(
                email="admin@suvinil.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrador Suvinil",
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
            
            # Criar usuário de demonstração
            demo = User(
                email="demo@suvinil.com",
                username="demo",
                hashed_password=get_password_hash("demo123"),
                full_name="Usuário Demonstração",
                role=UserRole.USER,
                is_active=True,
            )
            db.add(demo)
            
            db.commit()
            print("      Usuários criados:")
            print("      - Admin: admin / admin123")
            print("      - User:  user / user123")
            print("      - Demo:  demo / demo123")
        else:
            print("\n[2/3] Usuários já existem. Pulando...")
        
        # ========================================
        # CRIAR CATÁLOGO DE TINTAS
        # ========================================
        paint_count = db.query(Paint).count()
        
        if paint_count == 0:
            print(f"\n[3/3] Criando catálogo de tintas ({len(TINTAS_CATALOGO)} produtos)...")
            
            # Buscar usuário admin para created_by
            admin_user = db.query(User).filter(User.username == "admin").first()
            admin_id = admin_user.id if admin_user else None
            
            for i, paint_data in enumerate(TINTAS_CATALOGO, 1):
                paint = Paint(
                    **paint_data,
                    is_active=True,
                    created_by=admin_id,
                )
                db.add(paint)
                
                if i % 10 == 0:
                    print(f"      Criadas {i}/{len(TINTAS_CATALOGO)} tintas...")
            
            db.commit()
            print(f"      Catálogo completo: {len(TINTAS_CATALOGO)} tintas criadas!")
            
            # Mostrar resumo do catálogo
            print("\n      Resumo do catálogo:")
            print(f"      - Linha Premium: {len([t for t in TINTAS_CATALOGO if t['line'] == PaintLine.PREMIUM])} produtos")
            print(f"      - Linha Standard: {len([t for t in TINTAS_CATALOGO if t['line'] == PaintLine.STANDARD])} produtos")
            print(f"      - Linha Economy: {len([t for t in TINTAS_CATALOGO if t['line'] == PaintLine.ECONOMY])} produtos")
            print(f"      - Interiores: {len([t for t in TINTAS_CATALOGO if t['environment'] == Environment.INTERIOR])} produtos")
            print(f"      - Exteriores: {len([t for t in TINTAS_CATALOGO if t['environment'] == Environment.EXTERIOR])} produtos")
            print(f"      - Ambos: {len([t for t in TINTAS_CATALOGO if t['environment'] == Environment.BOTH])} produtos")
        else:
            print(f"\n[3/3] Banco já possui {paint_count} tintas. Pulando...")
        
        print("\n" + "=" * 60)
        print("   Banco de dados inicializado com sucesso!")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n   ERRO ao inicializar banco: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()

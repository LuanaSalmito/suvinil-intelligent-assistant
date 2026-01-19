"""
Sistema Multi-Agentes - Especialistas em Tintas Suvinil

Cada especialista tem expertise específica e usa ferramentas especializadas.
O Agente Orquestrador decide qual especialista consultar.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.repositories.paint_repository import PaintRepository
from app.models.paint import Environment, FinishType

logger = logging.getLogger(__name__)


class BaseSpecialist:
    """Classe base para todos os especialistas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.name = "Base Specialist"
        self.expertise = "Geral"
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """Determina se este especialista pode lidar com a query"""
        return False
    
    def consult(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa a consulta e retorna recomendações"""
        return {
            "specialist": self.name,
            "recommendations": [],
            "reasoning": "",
            "confidence": 0.0
        }


class InteriorEnvironmentSpecialist(BaseSpecialist):
    """
    Especialista em Ambientes Internos
    
    Expertise: Quartos, salas, escritórios, banheiros, cozinhas
    Foca em: Lavabilidade, sem odor, acabamentos delicados
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "Especialista em Ambientes Internos"
        self.expertise = "Ambientes internos: quartos, salas, escritórios, banheiros"
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """Verifica se é uma consulta sobre ambiente interno"""
        query_lower = query.lower()
        internal_keywords = [
            "quarto", "sala", "escritório", "escritorio", "banheiro", 
            "cozinha", "interno", "interna", "interior", "casa dentro"
        ]
        return any(keyword in query_lower for keyword in internal_keywords)
    
    def consult(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta especializada em ambientes internos"""
        logger.info(f"[{self.name}] Consultando para: {query[:50]}...")
        
        query_lower = query.lower()
        
        # Análise de necessidades específicas
        needs_washable = any(word in query_lower for word in ["lavável", "limpar", "limpeza", "fácil manutenção"])
        needs_no_odor = any(word in query_lower for word in ["sem cheiro", "sem odor", "odor", "cheiro"])
        is_bathroom = "banheiro" in query_lower
        is_bedroom = "quarto" in query_lower
        is_kids_room = any(word in query_lower for word in ["infantil", "criança", "bebê", "filho", "filha"])
        
        # Buscar tintas adequadas
        filters = {
            "environment": Environment.INTERIOR.value,
            "limit": 10
        }
        
        # Aplicar cor se especificada no contexto
        if context.get("color"):
            filters["color"] = context["color"]
        
        # Aplicar acabamento se especificado
        if context.get("finish_type"):
            filters["finish_type"] = context["finish_type"]
        
        paints = PaintRepository.search(self.db, **filters)
        
        # Filtrar por características especiais
        scored_paints = []
        for paint in paints:
            score = 0
            reasons = []
            
            features_lower = (paint.features or "").lower()
            
            # Scoring baseado em necessidades
            if needs_washable and "lavável" in features_lower:
                score += 3
                reasons.append("lavável")
            
            if needs_no_odor and "sem odor" in features_lower:
                score += 3
                reasons.append("sem odor")
            
            if is_bathroom and any(term in features_lower for term in ["anti-mofo", "antimofo", "umidade"]):
                score += 2
                reasons.append("resistente à umidade")
            
            if is_kids_room and any(term in features_lower for term in ["sem odor", "lavável", "atóxico"]):
                score += 2
                reasons.append("seguro para crianças")
            
            # Preferência por linha Premium se não houver restrição de preço
            if paint.line.value == "Premium":
                score += 1
            
            scored_paints.append({
                "paint": paint,
                "score": score,
                "reasons": reasons
            })
        
        # Ordenar por score
        scored_paints.sort(key=lambda x: x["score"], reverse=True)
        
        # Preparar recomendações
        recommendations = []
        for item in scored_paints[:3]:
            paint = item["paint"]
            recommendations.append({
                "paint_id": paint.id,
                "name": paint.name,
                "color": paint.color_name or paint.color,
                "finish": paint.finish_type.value,
                "line": paint.line.value,
                "price": paint.price,
                "features": paint.features,
                "match_reasons": item["reasons"],
                "score": item["score"]
            })
        
        # Gerar raciocínio
        reasoning_parts = [f"Analisando necessidades para ambiente interno"]
        if is_bedroom:
            reasoning_parts.append("Identificado: quarto. Priorizando conforto e saúde.")
        if is_bathroom:
            reasoning_parts.append("Identificado: banheiro. Priorizando resistência à umidade.")
        if needs_washable:
            reasoning_parts.append("Necessidade de lavabilidade detectada.")
        if needs_no_odor:
            reasoning_parts.append("Necessidade de tinta sem odor detectada.")
        if context.get("color"):
            reasoning_parts.append(f"Cor solicitada: {context['color']}")
        
        reasoning = " | ".join(reasoning_parts)
        
        confidence = min(1.0, len(recommendations) * 0.33)
        
        return {
            "specialist": self.name,
            "recommendations": recommendations,
            "reasoning": reasoning,
            "confidence": confidence,
            "context_used": ["environment", "needs", "color", "finish"]
        }


class ExteriorEnvironmentSpecialist(BaseSpecialist):
    """
    Especialista em Ambientes Externos
    
    Expertise: Fachadas, muros, varandas, áreas externas
    Foca em: Resistência climática, proteção UV, impermeabilização
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "Especialista em Ambientes Externos"
        self.expertise = "Ambientes externos: fachadas, muros, varandas"
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """Verifica se é uma consulta sobre ambiente externo"""
        query_lower = query.lower()
        external_keywords = [
            "fachada", "muro", "varanda", "externo", "externa", "exterior",
            "área externa", "sol", "chuva", "tempo"
        ]
        return any(keyword in query_lower for keyword in external_keywords)
    
    def consult(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta especializada em ambientes externos"""
        logger.info(f"[{self.name}] Consultando para: {query[:50]}...")
        
        query_lower = query.lower()
        
        # Análise de condições climáticas
        has_sun = any(word in query_lower for word in ["sol", "solar", "calor"])
        has_rain = any(word in query_lower for word in ["chuva", "chove", "úmido"])
        is_facade = "fachada" in query_lower
        
        # Buscar tintas adequadas
        filters = {
            "environment": Environment.EXTERIOR.value,
            "limit": 10
        }
        
        if context.get("color"):
            filters["color"] = context["color"]
        
        if context.get("finish_type"):
            filters["finish_type"] = context["finish_type"]
        
        paints = PaintRepository.search(self.db, **filters)
        
        # Scoring baseado em resistência climática
        scored_paints = []
        for paint in paints:
            score = 0
            reasons = []
            
            features_lower = (paint.features or "").lower()
            desc_lower = (paint.description or "").lower()
            
            # Resistência a intempéries
            if has_sun and any(term in features_lower for term in ["uv", "sol", "proteção solar"]):
                score += 3
                reasons.append("proteção solar")
            
            if has_rain and any(term in features_lower for term in ["chuva", "impermeável", "água"]):
                score += 3
                reasons.append("resistência à chuva")
            
            if any(term in features_lower for term in ["anti-mofo", "antimofo"]):
                score += 2
                reasons.append("anti-mofo")
            
            if "acrílica" in paint.name.lower() or "acrílica" in desc_lower:
                score += 2
                reasons.append("acrílica (durável)")
            
            # Premium para áreas externas é importante
            if paint.line.value == "Premium":
                score += 1
            
            scored_paints.append({
                "paint": paint,
                "score": score,
                "reasons": reasons
            })
        
        scored_paints.sort(key=lambda x: x["score"], reverse=True)
        
        recommendations = []
        for item in scored_paints[:3]:
            paint = item["paint"]
            recommendations.append({
                "paint_id": paint.id,
                "name": paint.name,
                "color": paint.color_name or paint.color,
                "finish": paint.finish_type.value,
                "line": paint.line.value,
                "price": paint.price,
                "features": paint.features,
                "match_reasons": item["reasons"],
                "score": item["score"]
            })
        
        reasoning_parts = ["Analisando necessidades para ambiente externo"]
        if is_facade:
            reasoning_parts.append("Fachada detectada. Priorizando durabilidade máxima.")
        if has_sun:
            reasoning_parts.append("Exposição solar detectada. Priorizando proteção UV.")
        if has_rain:
            reasoning_parts.append("Exposição à chuva detectada. Priorizando impermeabilização.")
        
        reasoning = " | ".join(reasoning_parts)
        confidence = min(1.0, len(recommendations) * 0.33)
        
        return {
            "specialist": self.name,
            "recommendations": recommendations,
            "reasoning": reasoning,
            "confidence": confidence,
            "context_used": ["environment", "weather", "surface"]
        }


class ColorAndFinishSpecialist(BaseSpecialist):
    """
    Especialista em Cores e Acabamentos
    
    Expertise: Psicologia das cores, harmonização, acabamentos
    Foca em: Escolha de cores, combinações, efeitos visuais
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "Especialista em Cores e Acabamentos"
        self.expertise = "Cores, acabamentos e harmonização"
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """Verifica se é uma consulta sobre cores ou acabamentos"""
        query_lower = query.lower()
        color_keywords = [
            "cor", "cores", "tom", "tonalidade", "azul", "verde", "vermelho",
            "amarelo", "branco", "cinza", "rosa", "roxo", "laranja",
            "acabamento", "fosco", "brilhante", "acetinado"
        ]
        return any(keyword in query_lower for keyword in color_keywords)
    
    def consult(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta especializada em cores e acabamentos"""
        logger.info(f"[{self.name}] Consultando para: {query[:50]}...")
        
        # Detectar cor solicitada
        color = context.get("color") or self._detect_color(query)
        finish = context.get("finish_type")
        
        if not color and not finish:
            # Listar cores disponíveis
            colors = PaintRepository.get_available_colors(self.db)
            return {
                "specialist": self.name,
                "recommendations": [],
                "reasoning": "Consulta sobre cores em geral. Listando opções disponíveis.",
                "confidence": 1.0,
                "available_colors": colors[:15]
            }
        
        # Buscar tintas pela cor
        filters = {"limit": 15}
        if color:
            filters["color"] = color
        if finish:
            filters["finish_type"] = finish
        
        paints = PaintRepository.search(self.db, **filters)
        
        recommendations = []
        for paint in paints[:5]:
            recommendations.append({
                "paint_id": paint.id,
                "name": paint.name,
                "color": paint.color_name or paint.color,
                "finish": paint.finish_type.value,
                "line": paint.line.value,
                "price": paint.price,
                "features": paint.features,
                "color_psychology": self._get_color_psychology(color) if color else None
            })
        
        reasoning = f"Buscando tintas"
        if color:
            reasoning += f" na cor {color}"
        if finish:
            reasoning += f" com acabamento {finish}"
        
        return {
            "specialist": self.name,
            "recommendations": recommendations,
            "reasoning": reasoning,
            "confidence": min(1.0, len(recommendations) * 0.2),
            "color_advice": self._get_color_psychology(color) if color else None
        }
    
    def _detect_color(self, query: str) -> Optional[str]:
        """Detecta cor mencionada na query"""
        query_lower = query.lower()
        color_map = {
            "azul": ["azul", "blue"],
            "vermelho": ["vermelho", "red"],
            "verde": ["verde", "green"],
            "amarelo": ["amarelo", "yellow"],
            "branco": ["branco", "white"],
            "cinza": ["cinza", "gray", "grey"],
            "rosa": ["rosa", "pink"],
            "roxo": ["roxo", "violeta", "lilás"],
            "laranja": ["laranja", "orange"],
            "marrom": ["marrom", "brown"],
            "bege": ["bege", "nude"],
        }
        
        for color_key, variations in color_map.items():
            if any(var in query_lower for var in variations):
                return color_key
        return None
    
    def _get_color_psychology(self, color: str) -> str:
        """Retorna informações sobre psicologia da cor"""
        psychology = {
            "azul": "Transmite calma, tranquilidade e profissionalismo. Ideal para quartos e escritórios.",
            "verde": "Representa natureza, equilíbrio e renovação. Ótimo para ambientes de relaxamento.",
            "vermelho": "Energia, paixão e vitalidade. Use com moderação em detalhes.",
            "amarelo": "Alegria, otimismo e criatividade. Excelente para cozinhas e áreas sociais.",
            "branco": "Pureza, amplitude e minimalismo. Versátil para todos os ambientes.",
            "cinza": "Modernidade, sofisticação e neutralidade. Perfeito para ambientes contemporâneos.",
            "rosa": "Delicadeza, aconchego e ternura. Ideal para quartos infantis e femininos.",
            "roxo": "Criatividade, luxo e espiritualidade. Ótimo para espaços criativos.",
            "laranja": "Entusiasmo, energia e sociabilidade. Ideal para áreas de convivência.",
            "bege": "Aconchego, neutralidade e elegância. Versátil e atemporal."
        }
        return psychology.get(color, "Cor versátil e interessante.")


class DurabilitySpecialist(BaseSpecialist):
    """
    Especialista em Durabilidade e Resistência
    
    Expertise: Superfícies especiais, resistência mecânica, durabilidade
    Foca em: Madeira, metal, alta resistência, superfícies desafiadoras
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "Especialista em Durabilidade"
        self.expertise = "Durabilidade, resistência e superfícies especiais"
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """Verifica se é uma consulta sobre durabilidade"""
        query_lower = query.lower()
        durability_keywords = [
            "madeira", "metal", "resistente", "durável", "duração",
            "calor", "desgaste", "tráfego", "resistência"
        ]
        return any(keyword in query_lower for keyword in durability_keywords)
    
    def consult(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta especializada em durabilidade"""
        logger.info(f"[{self.name}] Consultando para: {query[:50]}...")
        
        query_lower = query.lower()
        
        # Detectar tipo de superfície
        is_wood = "madeira" in query_lower
        is_metal = "metal" in query_lower
        needs_heat_resistance = "calor" in query_lower
        
        # Buscar todas as tintas
        paints = PaintRepository.get_all(self.db, limit=50)
        
        scored_paints = []
        for paint in paints:
            score = 0
            reasons = []
            
            surface = (paint.surface_type or "").lower()
            features = (paint.features or "").lower()
            name_lower = paint.name.lower()
            
            if is_wood and "madeira" in surface:
                score += 5
                reasons.append("específica para madeira")
            
            if is_metal and "metal" in surface:
                score += 5
                reasons.append("específica para metal")
            
            if needs_heat_resistance and "calor" in features:
                score += 3
                reasons.append("resistente ao calor")
            
            if "esmalte" in name_lower:
                score += 2
                reasons.append("esmalte sintético (alta durabilidade)")
            
            if "alta cobertura" in features:
                score += 1
                reasons.append("alta cobertura")
            
            if score > 0:
                scored_paints.append({
                    "paint": paint,
                    "score": score,
                    "reasons": reasons
                })
        
        scored_paints.sort(key=lambda x: x["score"], reverse=True)
        
        recommendations = []
        for item in scored_paints[:3]:
            paint = item["paint"]
            recommendations.append({
                "paint_id": paint.id,
                "name": paint.name,
                "color": paint.color_name or paint.color,
                "finish": paint.finish_type.value,
                "surface_type": paint.surface_type,
                "price": paint.price,
                "features": paint.features,
                "match_reasons": item["reasons"],
                "score": item["score"]
            })
        
        reasoning_parts = ["Analisando requisitos de durabilidade"]
        if is_wood:
            reasoning_parts.append("Superfície de madeira detectada.")
        if is_metal:
            reasoning_parts.append("Superfície metálica detectada.")
        if needs_heat_resistance:
            reasoning_parts.append("Necessidade de resistência ao calor.")
        
        reasoning = " | ".join(reasoning_parts)
        confidence = min(1.0, len(recommendations) * 0.33)
        
        return {
            "specialist": self.name,
            "recommendations": recommendations,
            "reasoning": reasoning,
            "confidence": confidence,
            "context_used": ["surface_type", "durability_needs"]
        }


def get_all_specialists(db: Session) -> List[BaseSpecialist]:
    """Retorna lista de todos os especialistas disponíveis"""
    return [
        InteriorEnvironmentSpecialist(db),
        ExteriorEnvironmentSpecialist(db),
        ColorAndFinishSpecialist(db),
        DurabilitySpecialist(db),
    ]

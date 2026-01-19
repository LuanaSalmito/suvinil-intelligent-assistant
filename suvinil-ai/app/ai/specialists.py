from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories.paint_repository import PaintRepository

class SpecialistRecommendation:
    def __init__(
        self,
        specialist_name: str,
        reasoning: str,
        recommended_paints: List[Any],
        confidence: float,
        key_attributes: List[str],
        technical_warnings: List[str] = None
    ):
        self.specialist_name = specialist_name
        self.reasoning = reasoning
        self.recommended_paints = recommended_paints
        self.confidence = confidence
        self.key_attributes = key_attributes
        self.technical_warnings = technical_warnings or []

    def to_dict(self) -> Dict:
        # Retorno retrocompatível (API e observabilidade)
        paint_ids = [getattr(p, "id", None) for p in self.recommended_paints]
        paint_ids = [pid for pid in paint_ids if pid is not None]
        return {
            "specialist": self.specialist_name,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "recommendations_count": len(self.recommended_paints),
            "paint_ids": paint_ids,
            "recommendations": [p.nome for p in self.recommended_paints],
            "warnings": self.technical_warnings,
            "key_attributes": self.key_attributes
        }

class BaseSpecialist:
    # Metadados (opcionais) para /status e observabilidade
    name: str = "Base Specialist"
    expertise: str = "Geral"

    def __init__(self, db: Session):
        self.db = db
        self.repository = PaintRepository

    def can_help(self, context: Dict) -> bool:
        """
        Determina se o especialista deve atuar.
        Default seguro: True (o próprio analyze() pode retornar None rapidamente).
        """
        return True

    def _get_base_candidates(self, context: Dict) -> List[Any]:
        """Recupera candidatos iniciais do banco para o especialista analisar."""
        return self.repository.recommend_candidates(
            self.db,
            environment=context.get("ambiente"),
            surface_type=context.get("tipo_parede"),
            color=context.get("cor"),
            finish_type=context.get("acabamento"),
            limit=200,
        )

class SurfaceExpert(BaseSpecialist):
    """Especialista em compatibilidade por superfície (madeira/metal/parede)."""
    name = "Especialista em Superfícies e Preparação"

    def can_help(self, context: Dict) -> bool:
        surf = (context.get("tipo_parede") or "").lower()
        return any(k in surf for k in ["madeira", "mdf", "ferro", "metal", "aço", "aco", "alumin", "inox", "parede", "alvenaria", "gesso"])

    def analyze(self, context: Dict) -> Optional[SpecialistRecommendation]:
        surface = (context.get("tipo_parede") or "").lower()
        cor = (context.get("cor") or "").lower()

        if not surface:
            return None

        candidates = self._get_base_candidates(context)
        if not candidates:
            return None

        # Reforçar substring por superfície (para casos onde tipo_parede no DB é composto)
        def surface_match(p) -> bool:
            hay = (getattr(p, "tipo_parede", "") or "").lower()
            if any(k in surface for k in ["ferro", "metal", "aço", "aco", "alumin", "inox"]):
                return any(k in hay for k in ["metal", "ferro", "aço", "aco", "alumin", "inox"])
            if any(k in surface for k in ["madeira", "mdf"]):
                return any(k in hay for k in ["madeira", "mdf"])
            if any(k in surface for k in ["parede", "alvenaria", "gesso", "reboco", "cimento"]):
                return any(k in hay for k in ["parede", "alvenaria", "gesso", "reboco", "cimento", "massa"])
            return surface in hay

        filtered = [p for p in candidates if surface_match(p)]
        if cor:
            filtered_color = [p for p in filtered if cor in (p.cor or "").lower()]
            filtered = filtered_color or filtered

        if not filtered:
            return None

        top_pick = filtered[0]
        return SpecialistRecommendation(
            specialist_name=self.name,
            reasoning=f"Para aplicar em {surface}, a {top_pick.nome} é compatível com a superfície e evita problemas de aderência/descascamento.",
            recommended_paints=[top_pick],
            confidence=0.93,
            key_attributes=["Compatibilidade de superfície", "Aderência"],
            technical_warnings=[],
        )

class ExteriorExpert(BaseSpecialist):
    """Especialista em Resistência Climática e Fachadas."""
    name = "Consultor de Engenharia Revestimento"
    
    def can_help(self, context: Dict) -> bool:
        env = (context.get("ambiente") or "").lower()
        surface = (context.get("tipo_parede") or "").lower()
        return any(x in env or x in surface for x in ["extern", "fachada", "muro", "varanda"])

    def analyze(self, context: Dict) -> Optional[SpecialistRecommendation]:
        env = (context.get("ambiente") or "").lower()
        surface = (context.get("tipo_parede") or "").lower()
        cor_solicitada = (context.get("cor") or "").lower()
        
        # Só atua se for ambiente externo ou fachada
        if not any(x in env or x in surface for x in ["extern", "fachada", "muro", "varanda"]):
            return None

        candidates = self._get_base_candidates(context)
        
        # Filtra por ambiente externo
        suitable = [
            p for p in candidates 
            if p.ambiente.value in ["Externo", "Interno/Externo"]
            and "madeira" not in (p.tipo_parede or "").lower()
        ]

        if not suitable: return None

        # PRIORIDADE: Se o usuário pediu uma cor, filtrar por ela primeiro
        if cor_solicitada:
            with_color = [p for p in suitable if cor_solicitada in (p.cor or "").lower()]
            if with_color:
                suitable = with_color
            else:
                # Não tem a cor pedida - informar na resposta
                top_pick = suitable[0]
                return SpecialistRecommendation(
                    specialist_name=self.name,
                    reasoning=f"Não encontrei uma tinta {cor_solicitada} para externo no catálogo. "
                              f"A opção mais próxima é {top_pick.nome} ({top_pick.cor}), que tem ótima resistência climática.",
                    recommended_paints=[top_pick],
                    confidence=0.7,
                    key_attributes=["Resistência Climática"],
                    technical_warnings=[f"Cor '{cor_solicitada}' não disponível para área externa"]
                )

        # Ordenação por robustez
        suitable.sort(key=lambda x: "sol" in (x.features or "").lower(), reverse=True)
        top_pick = suitable[0]

        reasoning = (
            f"Para sua varanda/área externa, recomendo a {top_pick.nome} na cor {top_pick.cor}. "
            f"Possui excelente resistência ao tempo e proteção UV."
        )

        return SpecialistRecommendation(
            specialist_name=self.name,
            reasoning=reasoning,
            recommended_paints=[top_pick],
            confidence=0.98,
            key_attributes=["Anti-mofo", "Proteção UV", "Resistente à chuva"]
        )

class ColorExpert(BaseSpecialist):
    """Especialista em Estética e Harmonização Visual."""
    name = "Curador de Estética Suvinil"

    def can_help(self, context: Dict) -> bool:
        return bool((context.get("cor") or "").strip())

    def analyze(self, context: Dict) -> Optional[SpecialistRecommendation]:
        cor = (context.get("cor") or "").lower()
        if not cor: return None

        # Simulação de base de conhecimento de design
        color_insights = {
            "rosa": "O Rosa transmite delicadeza e modernidade, ideal para criar pontos de acolhimento.",
            "cinza": "O Cinza Urbano é uma escolha minimalista que valoriza a luz natural.",
            "azul": "Tons de azul estimulam o foco, sendo excelentes para escritórios ou fachadas serenas.",
            "verde": "O Verde traz frescor e conexão com a natureza, perfeito para espaços de relaxamento.",
            "branco": "O Branco é atemporal e amplia visualmente os ambientes.",
            "amarelo": "O Amarelo traz energia e alegria, ideal para espaços de convivência.",
            "vermelho": "O Vermelho é ousado e vibrante, perfeito para criar pontos de destaque."
        }

        candidates = self._get_base_candidates(context)
        # Busca tintas que tenham a cor
        matches = [
            p for p in candidates 
            if cor in (p.cor or "").lower()
        ]

        if not matches:
            return SpecialistRecommendation(
                specialist_name=self.name,
                reasoning=f"A cor {cor} é excelente para {(context.get('ambiente') or 'o ambiente')}, mas precisamos validar a base química.",
                recommended_paints=[],
                confidence=0.6,
                key_attributes=["Tendência Visual"]
            )

        return SpecialistRecommendation(
            specialist_name=self.name,
            reasoning=color_insights.get(cor, f"A cor {cor} cria uma atmosfera personalizada e única."),
            recommended_paints=matches[:2],
            confidence=0.95,
            key_attributes=["Harmonização", "Estética Contemporânea"]
        )

class InteriorExpert(BaseSpecialist):
    """Especialista em Conforto Interno (Sem Odor/Lavável)."""
    name = "Especialista em Ambientes Internos"

    def can_help(self, context: Dict) -> bool:
        env = (context.get("ambiente") or "").lower()
        # Se explicitamente externo, não atua
        return "extern" not in env and "fachada" not in env and "varanda" not in env

    def analyze(self, context: Dict) -> Optional[SpecialistRecommendation]:
        env = (context.get("ambiente") or "").lower()
        cor_solicitada = (context.get("cor") or "").lower()
        
        if "extern" in env or "fachada" in env or "varanda" in env: 
            return None

        candidates = self._get_base_candidates(context)
        
        # Filtra por ambiente interno
        interior_paints = [
            p for p in candidates 
            if p.ambiente.value in ["Interno", "Interno/Externo"]
        ]

        if not interior_paints: return None

        # PRIORIDADE: Se o usuário pediu uma cor, filtrar por ela primeiro
        if cor_solicitada:
            with_color = [p for p in interior_paints if cor_solicitada in (p.cor or "").lower()]
            if with_color:
                interior_paints = with_color
            else:
                # Não tem a cor pedida
                top_pick = interior_paints[0]
                return SpecialistRecommendation(
                    specialist_name=self.name,
                    reasoning=f"Não encontrei uma tinta {cor_solicitada} para interno no catálogo. "
                              f"A opção mais próxima é {top_pick.nome} ({top_pick.cor}).",
                    recommended_paints=[top_pick],
                    confidence=0.7,
                    key_attributes=["Sem Odor"],
                    technical_warnings=[f"Cor '{cor_solicitada}' não disponível"]
                )

        # Score de aderência aos requisitos de saúde
        scored = []
        for p in interior_paints:
            score = 0
            feat = (p.features or "").lower()
            if "odor" in feat or "cheiro" in feat: score += 2
            if "lavável" in feat or "limp" in feat: score += 1
            scored.append((p, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        top_paints = [s[0] for s in scored[:2]]

        if top_paints:
            reasoning = f"Para o seu interior, recomendo a {top_paints[0].nome} na cor {top_paints[0].cor}."
        else:
            reasoning = "Não encontrei tintas adequadas para o ambiente interno."

        return SpecialistRecommendation(
            specialist_name=self.name,
            reasoning=reasoning,
            recommended_paints=top_paints,
            confidence=0.9,
            key_attributes=["Sem Odor", "Lavável"]
        )

def get_all_specialists(db: Session) -> List[BaseSpecialist]:
    """Factory para o Agente Orquestrador."""
    return [
        SurfaceExpert(db),
        ExteriorExpert(db),
        InteriorExpert(db),
        ColorExpert(db)
    ]
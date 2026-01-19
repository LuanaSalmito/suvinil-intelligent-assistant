import re
import logging
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_user_optional
from app.core.config import settings
from app.repositories.paint_repository import PaintRepository
from app.ai.rag_service import RAGService
from app.ai.image_generator import ImageGenerator
from app.models.chat_message import ChatMessage

logger = logging.getLogger(__name__)

router = APIRouter()

# Armazenar sessões de agentes por usuário (em produção, usar Redis)
_agent_sessions: Dict[int, Any] = {}
_orchestrator_sessions: Dict[Any, Any] = {}
_fallback_state: Dict[Any, Dict[str, Any]] = {}


# ============================================================================
# SCHEMAS DE REQUEST/RESPONSE
# ============================================================================

class ChatMessageRequest(BaseModel):
    """Schema de mensagem de entrada do chat"""
    message: str = Field(..., description="Mensagem do usuário", min_length=1, max_length=2000)
    reset_conversation: Optional[bool] = Field(False, description="Se True, reseta o histórico da conversa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Quero pintar meu quarto com uma cor clara e fácil de limpar",
                "reset_conversation": False
            }
        }


class ToolUsage(BaseModel):
    """Schema para uso de ferramenta pelo agente"""
    tool: str = Field(..., description="Nome da ferramenta utilizada")
    input: str = Field(..., description="Entrada passada para a ferramenta")


class SpecialistConsulted(BaseModel):
    """Schema para especialista consultado"""
    specialist: str = Field(..., description="Nome do especialista")
    confidence: float = Field(..., description="Nível de confiança da recomendação (0-1)")


class ReasoningStep(BaseModel):
    """Schema para etapa de raciocínio"""
    specialist: str = Field(..., description="Nome do especialista")
    reasoning: str = Field(..., description="Raciocínio do especialista")
    recommendations_count: int = Field(..., description="Número de recomendações fornecidas")


class ChatMetadata(BaseModel):
    """Metadados da execução do chat"""
    execution_time_ms: Optional[float] = Field(None, description="Tempo de execução em milissegundos")
    intermediate_steps_count: Optional[int] = Field(None, description="Número de passos intermediários")
    model: str = Field("gpt-4", description="Modelo de IA utilizado")
    mode: str = Field("orchestrator", description="Modo de operação (orchestrator, ai ou fallback)")
    specialists_consulted: Optional[List[SpecialistConsulted]] = Field(None, description="Especialistas consultados")
    reasoning_chain: Optional[List[ReasoningStep]] = Field(None, description="Cadeia de raciocínio completa")


class ChatResponse(BaseModel):
    """Schema de resposta do chat"""
    response: str = Field(..., description="Resposta do assistente")
    tools_used: List[ToolUsage] = Field(default_factory=list, description="Ferramentas utilizadas pelo agente")
    paints_mentioned: List[int] = Field(default_factory=list, description="IDs das tintas mencionadas")
    metadata: ChatMetadata = Field(..., description="Metadados da execução")
    image_url: Optional[str] = Field(None, description="URL da imagem gerada (quando visualização é solicitada)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Para ambientes internos como quartos, recomendo a **Suvinil Toque de Seda**...",
                "tools_used": [{"tool": "rag_search_paints", "input": "quarto lavável"}],
                "paints_mentioned": [1, 2],
                "metadata": {
                    "execution_time_ms": 1523.5,
                    "intermediate_steps_count": 2,
                    "model": "gpt-4",
                    "mode": "orchestrator"
                }
            }
        }


class ConversationHistoryItem(BaseModel):
    """Item do histórico de conversa"""
    role: str = Field(..., description="Role: 'user' ou 'assistant'")
    content: str = Field(..., description="Conteúdo da mensagem")
    timestamp: datetime = Field(..., description="Data/hora da mensagem")


class ConversationHistoryResponse(BaseModel):
    """Resposta do histórico de conversa"""
    messages: List[ConversationHistoryItem]
    total_count: int


class SimpleResponse(BaseModel):
    """Resposta simples"""
    message: str


class ReindexResponse(BaseModel):
    """Resposta do reindex do vector store"""
    message: str
    indexed_count: int


class VisualizationRequest(BaseModel):
    """Requisição para geração de visualização"""
    color: str = Field(..., description="Cor da tinta", min_length=1)
    environment: str = Field("sala", description="Tipo de ambiente (quarto, sala, fachada, etc.)")
    finish: str = Field("fosco", description="Tipo de acabamento (fosco, brilhante, acetinado)")
    paint_id: Optional[int] = Field(None, description="ID da tinta (opcional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "color": "azul",
                "environment": "quarto",
                "finish": "fosco",
                "paint_id": 1
            }
        }


class VisualizationResponse(BaseModel):
    """Resposta da geração de visualização"""
    image_url: str = Field(..., description="URL da imagem gerada")
    color: str = Field(..., description="Cor utilizada")
    environment: str = Field(..., description="Ambiente simulado")
    finish: str = Field(..., description="Acabamento aplicado")
    paint_info: Optional[Dict[str, Any]] = Field(None, description="Informações da tinta, se fornecido paint_id")


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def _is_openai_configured() -> bool:
    """Verifica se a OpenAI está configurada"""
    key = (settings.OPENAI_API_KEY or "").strip().strip('"').strip("'")
    # OpenAI keys normalmente começam com "sk-" (inclui "sk-proj-")
    return bool(key and key.startswith("sk-"))

def _persist_chat_turn(db: Session, user_id: Optional[int], user_text: str, assistant_text: str) -> None:
    """
    Persiste um turno (user + assistant) no banco para recuperar contexto depois.
    Só persiste para usuários autenticados (ChatMessage.user_id é NOT NULL).
    """
    if not user_id:
        return
    try:
        db.add(ChatMessage(user_id=user_id, role="user", content=user_text))
        db.add(ChatMessage(user_id=user_id, role="assistant", content=assistant_text))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Falha ao persistir histórico de chat (user_id={user_id}): {e}")

def _hydrate_orchestrator_memory_from_db(db: Session, user_id: Optional[int], orchestrator: Any, limit: int = 30) -> None:
    """
    Carrega histórico do banco para o orquestrador recuperar contexto após restart/reload.
    - Só para usuários autenticados (user_id int).
    - Não duplica hidratação dentro da mesma sessão.
    """
    if not user_id:
        return
    if getattr(orchestrator, "_db_hydrated", False):
        return
    try:
        msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )
        orchestrator.conversation_memory = [{"role": m.role, "content": m.content} for m in msgs]
        setattr(orchestrator, "_db_hydrated", True)
    except Exception as e:
        logger.warning(f"Falha ao hidratar memória do orquestrador (user_id={user_id}): {e}")

def _is_price_query(message: str) -> bool:
    """
    Detecta intenções de consulta de preço.
    Importante: usado para evitar chamadas ao LLM quando o usuário só quer valores do catálogo.
    """
    m = (message or "").strip().lower()
    if not m:
        return False
    keywords = ["preço", "preco", "valor", "custo", "quanto", "caro", "barato"]
    if any(k in m for k in keywords):
        return True
    # Exemplos comuns: "quanto custa", "qual o preço"
    return bool(re.search(r"\bquanto\s+custa\b|\bqual\s+o\s+pre[cç]o\b", m))


def _simple_chat_response(message: str, db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Resposta simples sem IA - usa busca no banco de dados.
    Fallback quando OpenAI não está configurada ou há erro.
    Mantém tom conversacional mesmo sem LLM.
    """
    message_lower = message.lower()
    paints = PaintRepository.get_all(db, skip=0, limit=100)
    paints_mentioned = []
    state = _fallback_state.setdefault(user_id or 0, {
        "last_paints": [],
        "last_color": None,
        "last_environment": None,
        "last_room_type": None,
        "last_age_context": None,
        # Ajuda a manter a conversa fluida (ex.: usuário responde "sim" / "pode")
        "pending_action": None,
    })
    
    # Buscar cores disponíveis no banco (cache)
    if "available_colors" not in state:
        available_colors = PaintRepository.get_available_colors(db)
        state["available_colors"] = available_colors

    def _is_affirmative(text: str) -> bool:
        t = (text or "").strip().lower()
        return t in {"sim", "s", "pode", "claro", "ok", "isso", "isso mesmo", "vamos", "manda"} or t.startswith("sim ")

    def _is_negative(text: str) -> bool:
        t = (text or "").strip().lower()
        return t in {"não", "nao", "n", "negativo"} or t.startswith("não ") or t.startswith("nao ")

    def _location_phrase() -> str:
        """Frase curta para o local, sem duplicar 'Para para ...'."""
        room = state.get("last_room_type")
        if room == "quarto":
            return "No quarto"
        if room == "sala":
            return "Na sala"
        if room == "cozinha":
            return "Na cozinha"
        if room == "banheiro":
            return "No banheiro"

        env = state.get("last_environment")
        if env == "interno":
            return "Em ambientes internos"
        if env == "externo":
            return "Em áreas externas"
        return "Para o seu projeto"

    def _pick_near_color_options(missing_color: str) -> List[str]:
        """Sugere até 2 cores existentes no catálogo como alternativa."""
        colors = state.get("available_colors", []) or []
        if not colors:
            return []

        def _first_match(keywords: List[str]) -> Optional[str]:
            for c in colors:
                hay = f"{c.get('color', '')} {c.get('color_display', '')}".lower()
                if any(k in hay for k in keywords):
                    return c.get("color_display") or c.get("color")
            return None

        options: List[str] = []
        miss = (missing_color or "").lower()

        if miss in {"roxo", "violeta", "lilás", "lilas"}:
            for keys in [["azul", "marinho", "anil"], ["rosa", "magenta", "fucsia", "fúcsia"], ["vinho", "bordo", "bordô"], ["cinza", "grafite"]]:
                pick = _first_match(keys)
                if pick and pick not in options:
                    options.append(pick)
        elif miss in {"rosa"}:
            for keys in [["pêssego", "pesego", "nude", "bege"], ["vermelho", "vinho"]]:
                pick = _first_match(keys)
                if pick and pick not in options:
                    options.append(pick)

        # Completar com as cores mais comuns, se ainda faltar opção
        for c in colors:
            if len(options) >= 2:
                break
            pick = c.get("color_display") or c.get("color")
            if pick and pick not in options:
                options.append(pick)

        return options[:2]

    def _set_pending_alternative_colors(missing_color: str, context_label: str):
        options = _pick_near_color_options(missing_color)
        state["pending_action"] = {
            "type": "suggest_alternative_colors",
            "missing_color": missing_color,
            "context_label": context_label,
            "options": options,
        }

    def _paint_text(paint) -> str:
        color_label = paint.cor or "cor variável"
        features_text = ""
        if paint.features:
            features_list = [f.strip() for f in paint.features.split(",") if f.strip()]
            features_text = ", ".join(features_list[:2])
        # Formato direto: nome, características principais
        response = f"{paint.nome} - {color_label}"
        if features_text:
            response += f", {features_text}"
        response += f", acabamento {paint.acabamento.value}"
        return response

    def _match_score(paint, keywords: List[str]) -> int:
        haystack = " ".join([
            paint.features or "",
            paint.nome or "",
        ]).lower()
        return sum(1 for keyword in keywords if keyword in haystack)

    def _filter_repeated(paints_list: List[Any]) -> List[Any]:
        if not user_id:
            return paints_list
        last_ids = set(state.get("last_paints", []))
        filtered = [p for p in paints_list if p.id not in last_ids]
        return filtered or paints_list

    def _is_wall_surface(paint) -> bool:
        surface = (paint.tipo_parede or "").lower()
        if not surface:
            return True
        return any(term in surface for term in ["parede", "alvenaria", "reboco", "gesso"])
    
    def _filter_by_color(paints_list: List[Any], color: str) -> List[Any]:
        """Filtra lista de tintas pela cor solicitada - retorna lista vazia se não encontrar"""
        if not color:
            return paints_list
        
        filtered = []
        for p in paints_list:
            color_in_paint = (p.cor or "").lower()
            
            # Verificar se a cor solicitada está no nome da cor
            if color in color_in_paint:
                filtered.append(p)
        
        # CRÍTICO: Retorna lista vazia se não encontrar, não a lista original
        return filtered

    def _detect_color_preference(text: str) -> Optional[str]:
        """Detecta a cor mencionada no texto"""
        color_map = {
            "azul": ["azul", "blue"],
            "vermelho": ["vermelho", "red", "vermelhao"],
            "verde": ["verde", "green"],
            "amarelo": ["amarelo", "yellow"],
            "branco": ["branco", "white"],
            "preto": ["preto", "black"],
            "cinza": ["cinza", "gray", "grey"],
            "rosa": ["rosa", "pink", "rosado", "rosada"],
            "roxo": ["roxo", "violeta", "lilas", "lilás", "roxa"],
            "laranja": ["laranja", "orange"],
            "marrom": ["marrom", "brown"],
            "bege": ["bege", "nude", "areia"],
            "turquesa": ["turquesa", "turquoise"],
        }
        
        for color_key, variations in color_map.items():
            if any(var in text for var in variations):
                return color_key
        return None

    # Se o usuário está respondendo uma pergunta pendente (ex.: "sim" / "pode"), tratar aqui.
    # (Importante: precisa vir depois das funções auxiliares acima.)
    pending = state.get("pending_action")
    if pending and pending.get("type") == "suggest_alternative_colors" and (_is_affirmative(message_lower) or _is_negative(message_lower)):
        if _is_negative(message_lower):
            state["pending_action"] = None
            response = "Tudo bem. Você tem alguma outra cor em mente (ex.: azul, cinza, bege) ou prefere que eu sugira um tom neutro?"
            return {
                "response": response,
                "tools_used": [],
                "paints_mentioned": [],
                "metadata": {
                    "execution_time_ms": 0,
                    "intermediate_steps_count": 0,
                    "model": "fallback",
                    "mode": "fallback"
                }
            }

        # Affirmative: escolher a primeira opção e tentar recomendar um produto real
        options = pending.get("options") or []
        chosen_color = (options[0] if options else None)
        alt_color = (options[1] if len(options) > 1 else None)

        # Limpar estado pendente e destravar o filtro de cor
        state["pending_action"] = None
        state["last_color"] = (chosen_color or "").lower() if chosen_color else None

        location = _location_phrase()
        interior_paints = [p for p in paints if p.ambiente.value in ["Interno", "Interno/Externo"]]
        interior_paints = [p for p in interior_paints if _is_wall_surface(p)] or interior_paints

        candidates = interior_paints
        if chosen_color:
            filtered = _filter_by_color(candidates, chosen_color.lower())
            if filtered:
                candidates = filtered
            elif alt_color:
                state["last_color"] = alt_color.lower()
                filtered2 = _filter_by_color(candidates, alt_color.lower())
                if filtered2:
                    candidates = filtered2

        candidates = _filter_repeated(candidates)
        if candidates:
            paint = candidates[0]
            paints_mentioned.append(paint.id)
            response = f"{location}, eu sugiro a {_paint_text(paint)}. Você prefere um tom mais escuro ou mais claro?"
        else:
            # Se não achou nada nem com alternativas, não insistir em cor.
            state["last_color"] = None
            any_paints = _filter_repeated(interior_paints)
            if any_paints:
                paint = any_paints[0]
                paints_mentioned.append(paint.id)
                response = f"{location}, eu sugiro a {_paint_text(paint)}. Qual cor você quer priorizar?"
            else:
                response = "Entendi. Me diz se é ambiente interno ou externo e o tipo de superfície, que eu sugiro a melhor opção do catálogo."

        if user_id and paints_mentioned:
            state["last_paints"] = paints_mentioned[:4]

        return {
            "response": response,
            "tools_used": [],
            "paints_mentioned": paints_mentioned,
            "metadata": {
                "execution_time_ms": 0,
                "intermediate_steps_count": 0,
                "model": "fallback",
                "mode": "fallback"
            }
        }
    
    # Detectar e armazenar contexto
    detected_color = _detect_color_preference(message_lower)
    if detected_color:
        state["last_color"] = detected_color
    if any(word in message_lower for word in ["interno", "interna", "interior"]):
        state["last_environment"] = "interno"
    if any(word in message_lower for word in ["externo", "externa", "exterior", "fachada", "muro", "varanda"]):
        state["last_environment"] = "externo"
    
    # Detectar tipo de ambiente específico
    if "quarto" in message_lower:
        state["last_room_type"] = "quarto"
    elif "sala" in message_lower:
        state["last_room_type"] = "sala"
    elif "banheiro" in message_lower:
        state["last_room_type"] = "banheiro"
    elif "cozinha" in message_lower:
        state["last_room_type"] = "cozinha"
    
    # Detectar contexto de idade/público
    if any(word in message_lower for word in ["filho", "filha", "criança", "anos", "infantil"]):
        # Tentar extrair idade
        age_match = re.search(r'(\d+)\s*anos?', message_lower)
        if age_match:
            state["last_age_context"] = f"criança de {age_match.group(1)} anos"
        else:
            state["last_age_context"] = "infantil"
    elif any(word in message_lower for word in ["bebê", "bebe", "recém-nascido"]):
        state["last_age_context"] = "bebê"
    elif any(word in message_lower for word in ["adolescente", "teen"]):
        state["last_age_context"] = "adolescente"

    if not paints:
        response = "Parece que ainda não temos tintas cadastradas no sistema. Assim que tiver produtos no catálogo, eu consigo te indicar a melhor opção."
        return {
            "response": response,
            "tools_used": [],
            "paints_mentioned": paints_mentioned,
            "metadata": {
                "execution_time_ms": 0,
                "intermediate_steps_count": 0,
                "model": "fallback",
                "mode": "fallback"
            }
        }
    
    # Respostas baseadas em palavras-chave - tom direto e consultivo
    if any(word in message_lower for word in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hey", "hello"]):
        response = f"Olá! Sou o assistente Suvinil. Temos {len(paints)} tintas disponíveis no catálogo. Me conta o que você precisa pintar?"

    elif any(word in message_lower for word in ["catálogo", "catalogo", "listar", "todas", "disponíveis"]):
        response = f"Olha só, temos {len(paints)} opções no catálogo! Vou te mostrar algumas das principais:\n\n"
        for paint in paints[:5]:  # Reduzido para não sobrecarregar
            response += f"**{paint.nome} - {paint.cor or 'Várias cores'}**\n"
            response += f"Ideal para: {paint.ambiente.value} | Acabamento: {paint.acabamento.value} | Linha: {paint.linha.value}\n"
            if paint.features:
                features_short = paint.features.split(',')[0].strip()  # Só primeira feature
                response += f"{features_short}\n"
            response += "\n"
            paints_mentioned.append(paint.id)
        if len(paints) > 5:
            response += f"Essas são só algumas! Tenho mais {len(paints) - 5} opções. Quer filtrar por algum ambiente específico ou tipo de acabamento?"
    
    elif any(word in message_lower for word in ["cores", "cor tem", "quais cores", "tem qual cor", "que cores"]):
        # Listar cores disponíveis do banco
        colors = state.get("available_colors", [])
        if colors:
            response = f"Temos {len(colors)} cores disponíveis no catálogo:\n\n"
            for color_info in colors[:10]:
                response += f"• {color_info['color_display']}: {color_info['count']} opções\n"
            if len(colors) > 10:
                response += f"\n... e mais {len(colors) - 10} cores. Qual cor você está procurando?"
            else:
                response += "\nQual cor você prefere?"
        else:
            response = "Me conte qual cor você está pensando que vou buscar no catálogo."
    
    elif any(word in message_lower for word in ["tem rosa", "rosa", "rosado", "rosada", "pink"]):
        # Se o usuário falou em fachada/muro/exterior, priorizar critérios técnicos (não só a cor)
        is_exterior_request = (
            state.get("last_environment") == "externo"
            or any(word in message_lower for word in ["fachada", "muro", "exterior", "externo", "externa"])
        )

        color_paints = [
            p for p in paints
            if any(term in (p.cor or "").lower() for term in ["rosa", "pink"])
            or any(term in (p.cor or "").lower() for term in ["rosa", "pink"])
        ]

        candidates = color_paints
        if is_exterior_request:
            # Fachada/muro: evitar recomendar produto de madeira e priorizar externo/ambos
            candidates = [p for p in candidates if p.ambiente.value in ["Externo", "Interno/Externo"]] or candidates
            candidates = [p for p in candidates if "madeira" not in (p.tipo_parede or "").lower()] or candidates
            # Preferir parede/alvenaria quando possível
            wall_candidates = [p for p in candidates if _is_wall_surface(p)]
            candidates = wall_candidates or candidates

        if candidates:
            candidates = _filter_repeated(candidates)
            paint = candidates[0]
            paints_mentioned.append(paint.id)
            if is_exterior_request:
                response = f"Para fachada em tom rosado, recomendo a {_paint_text(paint)}. Bate muito sol direto e pega chuva forte aí?"
            else:
                response = f"Sim! A {_paint_text(paint)}. É para ambiente interno ou externo?"
        else:
            _set_pending_alternative_colors("rosa", state.get("last_room_type") or "ambiente")
            options = state.get("pending_action", {}).get("options", [])
            if len(options) >= 2:
                response = f"No catálogo atual não encontrei rosa. Posso sugerir um tom de {options[0]} ou {options[1]} que fica próximo?"
            elif len(options) == 1:
                response = f"No catálogo atual não encontrei rosa. Posso sugerir um tom de {options[0]} que fica próximo?"
            else:
                response = "No catálogo atual não encontrei rosa. Posso sugerir cores próximas?"

    elif any(word in message_lower for word in ["tem roxo", "roxo", "roxa", "violeta", "lilás", "lilas"]):
        is_exterior_request = (
            state.get("last_environment") == "externo"
            or any(word in message_lower for word in ["fachada", "muro", "exterior", "externo", "externa"])
        )

        color_paints = [
            p for p in paints
            if any(term in (p.cor or "").lower() for term in ["roxo", "violeta", "lilás", "lilas"])
            or any(term in (p.cor or "").lower() for term in ["roxo", "violeta", "lilás", "lilas"])
        ]

        candidates = color_paints
        if is_exterior_request:
            candidates = [p for p in candidates if p.ambiente.value in ["Externo", "Interno/Externo"]] or candidates
            candidates = [p for p in candidates if "madeira" not in (p.tipo_parede or "").lower()] or candidates
            wall_candidates = [p for p in candidates if _is_wall_surface(p)]
            candidates = wall_candidates or candidates

        if candidates:
            candidates = _filter_repeated(candidates)
            paint = candidates[0]
            paints_mentioned.append(paint.id)
            if is_exterior_request:
                response = f"Para fachada, eu indicaria a {_paint_text(paint)}. Bate muito sol e chuva no local?"
            else:
                response = f"Sim! A {_paint_text(paint)}. É para ambiente interno ou externo?"
        else:
            _set_pending_alternative_colors("roxo", state.get("last_room_type") or "ambiente")
            options = state.get("pending_action", {}).get("options", [])
            if len(options) >= 2:
                response = f"No catálogo atual não encontrei roxo. Posso sugerir um tom de {options[0]} ou {options[1]} que fica próximo?"
            elif len(options) == 1:
                response = f"No catálogo atual não encontrei roxo. Posso sugerir um tom de {options[0]} que fica próximo?"
            else:
                response = "No catálogo atual não encontrei roxo. Posso sugerir cores próximas?"

    elif any(word in message_lower for word in ["balada", "festa", "club", "clube", "boate"]):
        interior_paints = [p for p in paints if p.ambiente.value in ["Interno", "Interno/Externo"]]
        interior_paints = [p for p in interior_paints if _is_wall_surface(p)] or interior_paints
        color_pref = state.get("last_color")
        if color_pref == "roxo":
            color_paints = [
                p for p in interior_paints
                if any(term in (p.cor or "").lower() for term in ["roxo", "violeta", "lilás", "lilas"])
                or any(term in (p.cor or "").lower() for term in ["roxo", "violeta", "lilás", "lilas"])
            ]
            interior_paints = color_paints or interior_paints
        interior_paints = _filter_repeated(interior_paints)
        if interior_paints:
            paint = interior_paints[0]
            paints_mentioned.append(paint.id)
            response = f"Para ambientes comerciais como baladas, recomendo a {_paint_text(paint)}. Você quer algo mais escuro ou vibrante?"
        else:
            response = "Me diz qual o tamanho do ambiente que ajusto a recomendação."

    elif any(word in message_lower for word in ["banheiro", "lavabo"]):
        interior_paints = [p for p in paints if p.ambiente.value in ["Interno", "Interno/Externo"]]
        interior_paints = [p for p in interior_paints if _is_wall_surface(p)] or interior_paints
        keywords = ["lavável", "lavavel", "anti-mofo", "antimofo", "mofo", "umidade", "resistente"]
        scored = sorted(
            interior_paints,
            key=lambda p: (_match_score(p, keywords), p.price or 0),
            reverse=True
        )
        picks = [p for p in scored if _match_score(p, keywords) > 0][:1] or scored[:1]
        if picks:
            picks = _filter_repeated(picks)
            paint = picks[0]
            paints_mentioned.append(paint.id)
            response = f"Para banheiros, recomendo a {_paint_text(paint)}. Você prefere acabamento fosco ou acetinado?"
        else:
            response = "Me conta se é um banheiro pequeno ou grande que ajusto a recomendação."

    elif "quarto" in message_lower and (
        any(word in message_lower for word in ["adolescente", "teen", "15 anos", "quinze", "15", "garoto", "menino", "filho", "filha", "criança", "anos"])
        or state.get("last_age_context")
    ):
        interior_paints = [p for p in paints if p.ambiente.value in ["Interno", "Interno/Externo"]]
        interior_paints = [p for p in interior_paints if _is_wall_surface(p)] or interior_paints
        keywords = ["lavável", "lavavel", "resistente", "sem odor", "sem cheiro"]
        
        # CRÍTICO: Sempre filtrar por cor se foi mencionada
        color_pref = state.get("last_color")
        if color_pref:
            color_filtered = _filter_by_color(interior_paints, color_pref)
            if color_filtered and len(color_filtered) > 0:
                interior_paints = color_filtered
            else:
                # Se não encontrou tintas na cor, informar
                age_context = state.get("last_age_context") or "criança"
                _set_pending_alternative_colors(color_pref, f"quarto de {age_context}")
                response = f"Não encontrei tintas na cor {color_pref} para quarto de {age_context}. Posso sugerir duas alternativas próximas?"
                return {
                    "response": response,
                    "tools_used": [],
                    "paints_mentioned": paints_mentioned,
                    "metadata": {
                        "execution_time_ms": 0,
                        "intermediate_steps_count": 0,
                        "model": "fallback",
                        "mode": "fallback"
                    }
                }
        
        scored = sorted(
            interior_paints,
            key=lambda p: (_match_score(p, keywords), p.price or 0),
            reverse=True
        )
        picks = [p for p in scored if _match_score(p, keywords) > 0][:1] or scored[:1]
        if picks:
            picks = _filter_repeated(picks)
            paint = picks[0]
            paints_mentioned.append(paint.id)
            
            # Usar contexto de idade se disponível
            age_context = state.get("last_age_context") or "criança"
            color_desc = f" na cor {color_pref}" if color_pref else ""
            response = f"Para quarto de {age_context}{color_desc}, recomendo a {_paint_text(paint)}. Você prefere acabamento fosco ou acetinado?"
        else:
            response = "Me conta se prefere algo mais neutro ou vibrante que ajusto a busca."

    elif any(word in message_lower for word in ["bebê", "bebe", "infantil"]):
        interior_paints = [p for p in paints if p.ambiente.value in ["Interno", "Interno/Externo"]]
        interior_paints = [p for p in interior_paints if _is_wall_surface(p)] or interior_paints
        keywords = ["sem odor", "sem cheiro", "lavável", "lavavel", "anti-mofo", "antimofo"]
        
        # CRÍTICO: Sempre filtrar por cor se foi mencionada
        color_pref = state.get("last_color")
        if color_pref:
            color_filtered = _filter_by_color(interior_paints, color_pref)
            if color_filtered and len(color_filtered) > 0:
                interior_paints = color_filtered
            else:
                # Se não encontrou tintas na cor, informar
                _set_pending_alternative_colors(color_pref, "quartos infantis")
                response = f"Não encontrei tintas na cor {color_pref} para quartos infantis. Posso sugerir duas alternativas próximas?"
                return {
                    "response": response,
                    "tools_used": [],
                    "paints_mentioned": paints_mentioned,
                    "metadata": {
                        "execution_time_ms": 0,
                        "intermediate_steps_count": 0,
                        "model": "fallback",
                        "mode": "fallback"
                    }
                }
        
        scored = sorted(
            interior_paints,
            key=lambda p: (_match_score(p, keywords), p.price or 0),
            reverse=True
        )
        picks = [p for p in scored if _match_score(p, keywords) > 0][:1] or scored[:1]
        if picks:
            picks = _filter_repeated(picks)
            paint = picks[0]
            paints_mentioned.append(paint.id)
            color_desc = f" na cor {color_pref}" if color_pref else ""
            response = f"Para quartos infantis{color_desc}, recomendo a {_paint_text(paint)}. Você prefere tons pastéis ou neutros?"
        else:
            response = "Me conta qual cor você está pensando que ajusto a busca."

    elif any(word in message_lower for word in ["interno", "interna", "quarto", "sala", "interior", "escritório"]):
        interior_paints = [p for p in paints if p.ambiente.value in ["Interno", "Interno/Externo"]]
        interior_paints = [p for p in interior_paints if _is_wall_surface(p)] or interior_paints
        
        # CRÍTICO: Sempre filtrar por cor se foi mencionada
        color_pref = state.get("last_color")
        if color_pref:
            color_filtered = _filter_by_color(interior_paints, color_pref)
            if color_filtered and len(color_filtered) > 0:
                interior_paints = color_filtered
            else:
                # Se não encontrou tintas na cor, informar
                context_desc = state.get("last_room_type") or "ambiente interno"
                _set_pending_alternative_colors(color_pref, context_desc)
                response = f"Não encontrei tintas na cor {color_pref} para {context_desc}. Posso sugerir duas alternativas próximas?"
                return {
                    "response": response,
                    "tools_used": [],
                    "paints_mentioned": paints_mentioned,
                    "metadata": {
                        "execution_time_ms": 0,
                        "intermediate_steps_count": 0,
                        "model": "fallback",
                        "mode": "fallback"
                    }
                }
        
        if interior_paints:
            interior_paints = _filter_repeated(interior_paints)
            paint = interior_paints[0]
            paints_mentioned.append(paint.id)
            
            # Construir descrição com contexto
            location = _location_phrase()
            
            color_desc = f" na cor {color_pref}" if color_pref else ""
            response = f"{location}{color_desc}, recomendo a {_paint_text(paint)}. Você prefere acabamento fosco ou acetinado?"
        else:
            response = "Me conta mais sobre o ambiente que ajusto a recomendação."
    
    elif any(word in message_lower for word in ["externo", "externa", "fachada", "exterior", "muro", "varanda"]):
        exterior_paints = [p for p in paints if p.ambiente.value in ["Externo", "Interno/Externo"]]
        
        # IMPORTANTE: Considerar a cor que o usuário pediu
        color_pref = state.get("last_color") or _detect_color_preference(message_lower)
        if color_pref:
            color_matches = _filter_by_color(exterior_paints, color_pref)
            if color_matches:
                exterior_paints = color_matches
            else:
                # Não tem a cor pedida para externo
                if exterior_paints:
                    alt_paint = exterior_paints[0]
                    paints_mentioned.append(alt_paint.id)
                    response = f"Não encontrei tinta {color_pref} para área externa no catálogo. A opção mais próxima é {_paint_text(alt_paint)}. Quer que eu busque outra cor?"
                else:
                    response = f"Não encontrei tinta {color_pref} para área externa. Qual outra cor você gostaria?"
                return {
                    "response": response,
                    "tools_used": [],
                    "paints_mentioned": paints_mentioned,
                    "metadata": {"execution_time_ms": 0, "mode": "fallback"}
                }
        
        if exterior_paints:
            exterior_paints = _filter_repeated(exterior_paints)
            paint = exterior_paints[0]
            paints_mentioned.append(paint.id)
            color_desc = f" na cor {paint.cor}" if paint.cor else ""
            response = f"Para áreas externas{color_desc}, recomendo a {_paint_text(paint)}. Bate muito sol direto no local?"
        else:
            response = "Me conta se é fachada ou muro que ajusto a recomendação."
    
    elif any(word in message_lower for word in ["preço", "preco", "valor", "custo", "quanto"]):
        response = "Aqui estão as tintas disponíveis no catálogo:\n\n"
        for paint in paints:
            response += f"• **{paint.nome} - {paint.cor or 'Cor variável'}** ({paint.linha.value})\n"
            paints_mentioned.append(paint.id)
    
    elif any(word in message_lower for word in ["lavável", "lavavel", "limpar", "limpeza"]):
        lavavel_paints = [p for p in paints if p.features and "lavável" in p.features.lower()]
        if lavavel_paints:
            response = "**Tintas Laváveis:**\n\n"
            for paint in lavavel_paints[:3]:
                response += f"• **{paint.nome}** - {paint.cor or 'Várias cores'}\n"
                response += f"  {paint.features}\n\n"
                paints_mentioned.append(paint.id)
        else:
            response = "Busque por características específicas e posso ajudá-lo a encontrar a tinta ideal."
    
    else:
        # Usar contexto armazenado para resposta mais inteligente
        context_parts = []
        
        # Se tem contexto de ambiente
        if state.get("last_room_type"):
            context_parts.append(_location_phrase().lower())
        elif state.get("last_environment"):
            context_parts.append(f"para ambiente {state['last_environment']}")
        
        # Se tem contexto de idade/público
        if state.get("last_age_context"):
            context_parts.append(f"(contexto: {state['last_age_context']})")
        
        if context_parts:
            # Tem contexto anterior - buscar com esse contexto
            context_query = " ".join(context_parts) + " " + message_lower
            interior_paints = [p for p in paints if p.ambiente.value in ["Interno", "Interno/Externo"]]
            
            # CRÍTICO: Sempre filtrar por cor se foi mencionada
            color_pref = state.get("last_color")
            if color_pref:
                color_filtered = _filter_by_color(interior_paints, color_pref)
                if color_filtered and len(color_filtered) > 0:
                    interior_paints = color_filtered
                else:
                    # Se não encontrou tintas na cor, informar
                    context_desc = " ".join(context_parts)
                    _set_pending_alternative_colors(color_pref, context_desc)
                    response = f"{context_desc.capitalize()}, não encontrei tintas na cor {color_pref}. Posso sugerir duas alternativas próximas?"
                    return {
                        "response": response,
                        "tools_used": [],
                        "paints_mentioned": paints_mentioned,
                        "metadata": {
                            "execution_time_ms": 0,
                            "intermediate_steps_count": 0,
                            "model": "fallback",
                            "mode": "fallback"
                        }
                    }
            
            # Tentar encontrar uma tinta relevante
            keywords = message_lower.split()
            scored = sorted(
                interior_paints,
                key=lambda p: (_match_score(p, keywords), p.price or 0),
                reverse=True
            )
            
            if scored:
                scored = _filter_repeated(scored)
                paint = scored[0]
                paints_mentioned.append(paint.id)
                context_desc = " ".join(context_parts)
                color_desc = f" na cor {color_pref}" if color_pref else ""
                response = f"{context_desc.capitalize()}{color_desc}, recomendo a {_paint_text(paint)}. É isso que você procura?"
            else:
                response = f"Entendi que é {' '.join(context_parts)}. Me conta mais sobre o que você procura (cor, acabamento, características)?"
        else:
            # Sem contexto anterior - perguntar
            response = "Me conta mais sobre o que você precisa: é para ambiente interno ou externo? Qual o tipo de superfície?"
    
    if user_id and paints_mentioned:
        state["last_paints"] = paints_mentioned[:4]

    return {
        "response": response,
        "tools_used": [],
        "paints_mentioned": paints_mentioned,
        "metadata": {
            "execution_time_ms": 0,
            "intermediate_steps_count": 0,
            "model": "fallback",
            "mode": "fallback"
        }
    }


def get_orchestrator_service(session_key: Any, db: Session, reset: bool = False):
    """Obtém ou cria serviço de orquestrador para o usuário/sessão"""
    if not _is_openai_configured():
        return None
    
    # Importar apenas se OpenAI estiver configurada
    from app.ai.orchestrator import OrchestratorAgent
    
    if reset or session_key not in _orchestrator_sessions:
        try:
            # user_id pode ser None (usuário anônimo); session_key garante isolamento de memória
            _orchestrator_sessions[session_key] = OrchestratorAgent(db, user_id=(session_key if isinstance(session_key, int) else None))
        except Exception as e:
            print(f"Erro ao criar OrchestratorAgent: {e}")
            return None
    return _orchestrator_sessions[session_key]


def get_agent_service(user_id: int, db: Session, reset: bool = False):
    """Obtém ou cria serviço de agente para o usuário (legacy, usar orchestrator)"""
    if not _is_openai_configured():
        return None
    
    # Importar apenas se OpenAI estiver configurada
    try:
        from app.ai.agent_service import AgentService
    except ModuleNotFoundError:
        # Código legado removido/renomeado em refactors; manter endpoint estável
        return None
    
    if reset or user_id not in _agent_sessions:
        try:
            _agent_sessions[user_id] = AgentService(db, user_id=user_id)
        except Exception as e:
            print(f"Erro ao criar AgentService: {e}")
            return None
    return _agent_sessions[user_id]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Enviar mensagem para o assistente (Sistema Multi-Agentes)",
    description="""
Envia uma mensagem para o Assistente Inteligente Suvinil e recebe uma resposta personalizada
através de um sistema multi-agentes com orquestrador.

**Sistema de Especialistas:**
- Especialista em Ambientes Internos (quartos, salas, banheiros)
- Especialista em Ambientes Externos (fachadas, muros, varandas)
- Especialista em Cores e Acabamentos (psicologia das cores)
- Especialista em Durabilidade (madeira, metal, resistência)

O orquestrador analisa sua mensagem, consulta os especialistas apropriados
e combina suas recomendações para fornecer a melhor resposta.

**Exemplo de perguntas:**
- "Quero pintar meu quarto, algo fácil de limpar e sem cheiro forte"
- "Preciso de uma tinta para fachada, bate muito sol"
- "Tem tinta para madeira resistente ao calor?"
- "Mostra como ficaria minha varanda de azul claro"

**Resposta inclui:**
- Recomendações personalizadas
- Raciocínio dos especialistas consultados
- Observabilidade completa do processo de decisão
    """
)
async def chat(
    chat_message: ChatMessageRequest,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Endpoint principal de chat com Sistema Multi-Agentes"""
    
    # Usar ID None para usuários anônimos (mas isolar a memória por sessão)
    user_id = current_user["id"] if current_user else None
    if user_id is None:
        ua = (request.headers.get("user-agent") or "").encode("utf-8")
        ua_hash = hashlib.sha256(ua).hexdigest()[:10]
        client_host = getattr(getattr(request, "client", None), "host", "unknown")
        session_key: Any = f"anon:{client_host}:{ua_hash}"
    else:
        session_key = user_id

    # Preço: responder direto do catálogo (sem IA), mesmo com OpenAI configurada.
    if _is_price_query(chat_message.message):
        result = _simple_chat_response(chat_message.message, db, user_id=session_key)
        return ChatResponse(
            response=result["response"],
            tools_used=[ToolUsage(**t) for t in result["tools_used"]],
            paints_mentioned=result["paints_mentioned"],
            metadata=ChatMetadata(**result["metadata"])
        )
    
    # Verificar se OpenAI está configurada
    if not _is_openai_configured():
        # Usar modo simples sem IA
        result = _simple_chat_response(chat_message.message, db, user_id=session_key)
        return ChatResponse(
            response=result["response"],
            tools_used=[ToolUsage(**t) for t in result["tools_used"]],
            paints_mentioned=result["paints_mentioned"],
            metadata=ChatMetadata(**result["metadata"])
        )
    
    # Modo com Orquestrador Multi-Agentes
    orchestrator = get_orchestrator_service(
        session_key,
        db,
        reset=chat_message.reset_conversation,
    )
    
    if orchestrator is None:
        # Fallback para modo simples se houver erro ao criar orquestrador
        result = _simple_chat_response(chat_message.message, db, user_id=session_key)
        return ChatResponse(
            response=result["response"],
            tools_used=[ToolUsage(**t) for t in result["tools_used"]],
            paints_mentioned=result["paints_mentioned"],
            metadata=ChatMetadata(**result["metadata"])
        )
    
    if chat_message.reset_conversation:
        orchestrator.reset_memory()
        # Evitar re-hidratar do banco no mesmo request após reset explícito
        setattr(orchestrator, "_db_hydrated", True)
    else:
        # Carregar histórico do banco (usuário logado) para manter contexto consistente
        _hydrate_orchestrator_memory_from_db(db, user_id, orchestrator, limit=30)
    
    try:
        # Executar orquestrador (agora é async)
        result = await orchestrator.chat(chat_message.message)
        
        # Converter specialists_consulted para schema
        specialists_consulted = [
            SpecialistConsulted(
                specialist=s.get("specialist", ""),
                confidence=s.get("confidence", 0.0)
            )
            for s in result.get("specialists_consulted", [])
        ]
        
        # Converter reasoning_chain para schema
        reasoning_chain = [
            ReasoningStep(
                specialist=r.get("specialist", ""),
                reasoning=r.get("reasoning", ""),
                recommendations_count=r.get("recommendations_count", 0)
            )
            for r in result.get("reasoning_chain", [])
        ]
        
        metadata = ChatMetadata(
            execution_time_ms=result.get("metadata", {}).get("execution_time_ms"),
            intermediate_steps_count=len(reasoning_chain),
            model="gpt-4",
            mode="orchestrator",
            specialists_consulted=specialists_consulted,
            reasoning_chain=reasoning_chain
        )
        
        response = ChatResponse(
            response=result.get("response", ""),
            tools_used=[ToolUsage(**t) for t in result.get("tools_used", [])],
            paints_mentioned=result.get("paints_mentioned", []),
            metadata=metadata
        )
        
        # Se gerou imagem, adicionar ao response (extensão do schema)
        if "image_url" in result:
            response.image_url = result["image_url"]

        # Persistir histórico (usuário autenticado) para manter memória pós-restart
        _persist_chat_turn(db, user_id, chat_message.message, response.response)
        
        return response
        
    except Exception as e:
        # Em caso de erro no orquestrador, usar modo simples
        print(f"Erro no orquestrador: {e}")
        import traceback
        traceback.print_exc()
        
        result = _simple_chat_response(chat_message.message, db, user_id=session_key)
        # Persistir também o fallback para histórico do usuário (se autenticado)
        _persist_chat_turn(db, user_id, chat_message.message, result.get("response", ""))
        return ChatResponse(
            response=result["response"],
            tools_used=[ToolUsage(**t) for t in result["tools_used"]],
            paints_mentioned=result["paints_mentioned"],
            metadata=ChatMetadata(**result["metadata"])
        )


@router.post(
    "/chat/reset",
    response_model=SimpleResponse,
    summary="Resetar conversa",
    description="Reseta o histórico de conversa do usuário atual."
)
async def reset_chat(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reseta conversa do chat"""
    # Resetar orquestrador
    if current_user["id"] in _orchestrator_sessions:
        _orchestrator_sessions[current_user["id"]].reset_memory()
        del _orchestrator_sessions[current_user["id"]]
    
    # Resetar agente legacy
    if current_user["id"] in _agent_sessions:
        _agent_sessions[current_user["id"]].reset_memory()
        del _agent_sessions[current_user["id"]]
    
    # Resetar fallback state
    if current_user["id"] in _fallback_state:
        del _fallback_state[current_user["id"]]
    
    return SimpleResponse(message="Conversa resetada com sucesso!")


@router.get(
    "/chat/history",
    response_model=ConversationHistoryResponse,
    summary="Obter histórico de conversa",
    description="Retorna o histórico de mensagens do usuário atual."
)
async def get_chat_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Obtém histórico de conversas do usuário"""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user["id"])
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    
    # Inverter para ordem cronológica
    messages = list(reversed(messages))
    
    return ConversationHistoryResponse(
        messages=[
            ConversationHistoryItem(
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at
            )
            for msg in messages
        ],
        total_count=len(messages)
    )


@router.delete(
    "/chat/history",
    response_model=SimpleResponse,
    summary="Limpar histórico de conversa",
    description="Remove todo o histórico de mensagens do usuário atual."
)
async def clear_chat_history(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Limpa histórico de conversas do usuário"""
    try:
        db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user["id"]
        ).delete()
        db.commit()
        
        # Limpar sessão do orquestrador
        if current_user["id"] in _orchestrator_sessions:
            _orchestrator_sessions[current_user["id"]].reset_memory()
            del _orchestrator_sessions[current_user["id"]]
        
        # Limpar sessão do agente legacy
        if current_user["id"] in _agent_sessions:
            _agent_sessions[current_user["id"]].reset_memory()
            del _agent_sessions[current_user["id"]]
        
        # Limpar fallback state
        if current_user["id"] in _fallback_state:
            del _fallback_state[current_user["id"]]
        
        return SimpleResponse(message="Histórico de conversa limpo com sucesso!")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar histórico: {str(e)}")


@router.get(
    "/status",
    summary="Status do serviço de IA",
    description="Verifica o status do serviço de IA e se está configurado corretamente."
)
async def get_ai_status(db: Session = Depends(get_db)):
    """Retorna status do serviço de IA"""
    openai_configured = _is_openai_configured()
    
    specialists_info = []
    if openai_configured:
        try:
            from app.ai.specialists import get_all_specialists
            specialists = get_all_specialists(db)
            specialists_info = [
                {
                    "name": s.name,
                    "expertise": s.expertise
                }
                for s in specialists
            ]
        except Exception as e:
            logger.warning(f"Erro ao obter especialistas: {e}")
    
    return {
        "service": "suvinil-ai-chat",
        "status": "healthy",
        "ai_enabled": openai_configured,
        "architecture": "multi-agent-orchestrator" if openai_configured else "fallback",
        "model": "gpt-4" if openai_configured else "fallback",
        "specialists": specialists_info,
        "features": {
            "multi_agent_system": openai_configured,
            "semantic_search_rag": openai_configured,
            "image_generation_dalle": openai_configured,
            "conversation_memory": True,
            "reasoning_observability": openai_configured,
            "specialist_consultation": openai_configured,
        },
        "message": "Sistema Multi-Agentes totalmente funcional" if openai_configured else "Modo fallback - configure OPENAI_API_KEY para IA completa"
    }


@router.post(
    "/rag/reindex",
    response_model=ReindexResponse,
    summary="Reindexar vector store",
    description="Recria o vector store a partir do catálogo atual de tintas."
)
async def reindex_rag(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reindexa o vector store do RAG"""
    rag_service = RAGService(db)
    indexed_count = rag_service.reindex()
    return ReindexResponse(
        message="Vector store atualizado com sucesso.",
        indexed_count=indexed_count
    )


@router.post(
    "/visualize",
    response_model=VisualizationResponse,
    summary="Gerar visualização de tinta aplicada (DALL-E)",
    description="""
Gera uma imagem usando DALL-E mostrando como a tinta ficaria aplicada em um ambiente.

**Recurso Especial:**
Permite ao usuário visualizar a cor escolhida antes de comprar, simulando
a aplicação da tinta em diferentes ambientes.

**Parâmetros:**
- color: Cor da tinta (azul, verde, vermelho, etc.)
- environment: Tipo de ambiente (quarto, sala, fachada, etc.)
- finish: Tipo de acabamento (fosco, brilhante, acetinado)
- paint_id: ID da tinta (opcional, para incluir informações do produto)

**Exemplos:**
```json
{
  "color": "azul",
  "environment": "quarto",
  "finish": "fosco"
}
```

**Nota:** Este recurso requer OPENAI_API_KEY configurada e consome créditos da API.
    """
)
async def generate_visualization(
    request: VisualizationRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Gera visualização de tinta aplicada usando DALL-E"""
    
    if not _is_openai_configured():
        raise HTTPException(
            status_code=503,
            detail="Geração de imagens não disponível. Configure OPENAI_API_KEY."
        )
    
    try:
        # Criar gerador de imagens
        generator = ImageGenerator()
        
        # Gerar imagem
        image_url = await generator.generate_paint_visualization(
            color=request.color,
            environment=request.environment,
            finish=request.finish
        )
        
        # Se paint_id foi fornecido, buscar informações da tinta
        paint_info = None
        if request.paint_id:
            paint = PaintRepository.get_by_id(db, request.paint_id)
            if paint:
                paint_info = {
                    "id": paint.id,
                    "nome": paint.nome,
                    "cor": paint.cor,
                    "acabamento": paint.acabamento.value,
                    "linha": paint.linha.value,
                    "features": paint.features
                }
        
        return VisualizationResponse(
            image_url=image_url,
            color=request.color,
            environment=request.environment,
            finish=request.finish,
            paint_info=paint_info
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar visualização: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar visualização: {str(e)}"
        )

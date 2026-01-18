"""
Endpoints de Chat com IA - Assistente Inteligente Suvinil

Este módulo expõe a API do chatbot inteligente de tintas,
com suporte a:
- Conversação natural
- Histórico persistente
- Recomendações personalizadas
- Geração de visualizações
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.config import settings
from app.repositories.paint_repository import PaintRepository
from app.models.chat_message import ChatMessage

router = APIRouter()

# Armazenar sessões de agentes por usuário (em produção, usar Redis)
_agent_sessions: Dict[int, Any] = {}


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


class ChatMetadata(BaseModel):
    """Metadados da execução do chat"""
    execution_time_ms: Optional[float] = Field(None, description="Tempo de execução em milissegundos")
    intermediate_steps_count: Optional[int] = Field(None, description="Número de passos intermediários")
    model: str = Field("gpt-4o-mini", description="Modelo de IA utilizado")
    mode: str = Field("ai", description="Modo de operação (ai ou fallback)")


class ChatResponse(BaseModel):
    """Schema de resposta do chat"""
    response: str = Field(..., description="Resposta do assistente")
    tools_used: List[ToolUsage] = Field(default_factory=list, description="Ferramentas utilizadas pelo agente")
    paints_mentioned: List[int] = Field(default_factory=list, description="IDs das tintas mencionadas")
    metadata: ChatMetadata = Field(..., description="Metadados da execução")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Para ambientes internos como quartos, recomendo a **Suvinil Toque de Seda**...",
                "tools_used": [{"tool": "search_paints", "input": "quarto lavável"}],
                "paints_mentioned": [1, 2],
                "metadata": {
                    "execution_time_ms": 1523.5,
                    "intermediate_steps_count": 2,
                    "model": "gpt-4o-mini",
                    "mode": "ai"
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


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def _is_openai_configured() -> bool:
    """Verifica se a OpenAI está configurada"""
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))


def _simple_chat_response(message: str, db: Session) -> Dict[str, Any]:
    """
    Resposta simples sem IA - usa busca no banco de dados.
    Fallback quando OpenAI não está configurada ou há erro.
    """
    message_lower = message.lower()
    paints = PaintRepository.get_all(db, skip=0, limit=100)
    paints_mentioned = []
    
    if not paints:
        response = "Olá! Sou o assistente Suvinil. No momento não há tintas cadastradas no sistema. Por favor, adicione algumas tintas para que eu possa ajudá-lo."
    
    # Respostas baseadas em palavras-chave
    elif any(word in message_lower for word in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hey", "hello"]):
        response = f"""Olá! 👋 Sou o **Assistente Virtual Suvinil**, seu especialista em tintas!

Posso ajudá-lo a:
• Encontrar a tinta ideal para seu projeto
• Recomendar produtos para ambientes internos ou externos
• Sugerir cores e acabamentos
• Comparar produtos

Temos **{len(paints)} tintas** disponíveis no catálogo. Como posso ajudar você hoje?"""

    elif any(word in message_lower for word in ["catálogo", "catalogo", "listar", "todas", "disponíveis"]):
        response = "**Catálogo de Tintas Suvinil:**\n\n"
        for paint in paints[:10]:
            response += f"• **{paint.name}** - {paint.color_name or 'Cor variável'}\n"
            response += f"  Ambiente: {paint.environment.value} | Acabamento: {paint.finish_type.value}\n"
            paints_mentioned.append(paint.id)
        if len(paints) > 10:
            response += f"\n*...e mais {len(paints) - 10} produtos*"
    
    elif any(word in message_lower for word in ["interno", "interna", "quarto", "sala", "interior", "escritório"]):
        interior_paints = [p for p in paints if p.environment.value in ["interno", "ambos"]]
        if interior_paints:
            response = "**Recomendações para ambientes internos:**\n\n"
            for paint in interior_paints[:3]:
                response += f"• **{paint.name}** - {paint.color_name or paint.color}\n"
                response += f"  {paint.description or 'Tinta de qualidade para interiores.'}\n\n"
                paints_mentioned.append(paint.id)
        else:
            response = "Não encontrei tintas específicas para ambientes internos no momento."
    
    elif any(word in message_lower for word in ["externo", "externa", "fachada", "exterior", "muro", "varanda"]):
        exterior_paints = [p for p in paints if p.environment.value in ["externo", "ambos"]]
        if exterior_paints:
            response = "**Recomendações para ambientes externos:**\n\n"
            for paint in exterior_paints[:3]:
                response += f"• **{paint.name}** - {paint.color_name or paint.color}\n"
                response += f"  {paint.description or 'Tinta resistente para exteriores.'}\n\n"
                paints_mentioned.append(paint.id)
        else:
            response = "Não encontrei tintas específicas para ambientes externos no momento."
    
    elif any(word in message_lower for word in ["preço", "preco", "valor", "custo", "quanto"]):
        response = "**Preços das Tintas Suvinil:**\n\n"
        for paint in paints:
            if paint.price:
                response += f"• **{paint.name}**: R$ {paint.price:.2f}\n"
                paints_mentioned.append(paint.id)
    
    elif any(word in message_lower for word in ["lavável", "lavavel", "limpar", "limpeza"]):
        lavavel_paints = [p for p in paints if p.features and "lavável" in p.features.lower()]
        if lavavel_paints:
            response = "**Tintas Laváveis:**\n\n"
            for paint in lavavel_paints[:3]:
                response += f"• **{paint.name}** - {paint.color_name or 'Várias cores'}\n"
                response += f"  {paint.features}\n\n"
                paints_mentioned.append(paint.id)
        else:
            response = "Busque por características específicas e posso ajudá-lo a encontrar a tinta ideal."
    
    else:
        response = f"""Entendi! Posso ajudá-lo a encontrar a tinta ideal.

Temos **{len(paints)} tintas** disponíveis. Você pode me perguntar sobre:

• Tintas para **ambientes internos** (quartos, salas, escritórios)
• Tintas para **ambientes externos** (fachadas, muros, varandas)
• Tintas **laváveis** ou com características específicas
• **Listar** todas as tintas disponíveis
• Consultar **preços**

O que você gostaria de saber?"""
    
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


def get_agent_service(user_id: int, db: Session, reset: bool = False):
    """Obtém ou cria serviço de agente para o usuário"""
    if not _is_openai_configured():
        return None
    
    # Importar apenas se OpenAI estiver configurada
    from app.ai.agent_service import AgentService
    
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
    summary="Enviar mensagem para o assistente",
    description="""
Envia uma mensagem para o Assistente Inteligente Suvinil e recebe uma resposta personalizada.

O assistente pode:
- Recomendar tintas baseado nas suas necessidades
- Buscar produtos por características (lavável, sem odor, etc.)
- Filtrar por ambiente (interno/externo)
- Comparar produtos
- Gerar visualizações (quando solicitado)
- Sugerir cores e acabamentos

**Exemplo de perguntas:**
- "Quero pintar meu quarto, algo fácil de limpar e sem cheiro forte"
- "Preciso de uma tinta para fachada, bate muito sol"
- "Tem tinta para madeira resistente ao calor?"
- "Mostra como ficaria minha varanda de azul claro"
    """
)
async def chat(
    chat_message: ChatMessageRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Endpoint principal de chat com IA"""
    
    # Verificar se OpenAI está configurada
    if not _is_openai_configured():
        # Usar modo simples sem IA
        result = _simple_chat_response(chat_message.message, db)
        return ChatResponse(
            response=result["response"],
            tools_used=[ToolUsage(**t) for t in result["tools_used"]],
            paints_mentioned=result["paints_mentioned"],
            metadata=ChatMetadata(**result["metadata"])
        )
    
    # Modo com IA
    agent_service = get_agent_service(
        current_user["id"],
        db,
        reset=chat_message.reset_conversation,
    )
    
    if agent_service is None:
        # Fallback para modo simples se houver erro ao criar agente
        result = _simple_chat_response(chat_message.message, db)
        return ChatResponse(
            response=result["response"],
            tools_used=[ToolUsage(**t) for t in result["tools_used"]],
            paints_mentioned=result["paints_mentioned"],
            metadata=ChatMetadata(**result["metadata"])
        )
    
    if chat_message.reset_conversation:
        agent_service.reset_memory()
    
    try:
        # Executar agente
        result = agent_service.chat(chat_message.message)
        
        # Converter para schema de resposta
        tools_used = [
            ToolUsage(tool=t.get("tool", ""), input=str(t.get("input", "")))
            for t in result.get("tools_used", [])
        ]
        
        metadata = ChatMetadata(
            execution_time_ms=result.get("metadata", {}).get("execution_time_ms"),
            intermediate_steps_count=result.get("metadata", {}).get("intermediate_steps_count"),
            model="gpt-4o-mini",
            mode="ai"
        )
        
        return ChatResponse(
            response=result.get("response", ""),
            tools_used=tools_used,
            paints_mentioned=result.get("paints_mentioned", []),
            metadata=metadata
        )
        
    except Exception as e:
        # Em caso de erro na IA, usar modo simples
        print(f"Erro no agente IA: {e}")
        result = _simple_chat_response(chat_message.message, db)
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
    if current_user["id"] in _agent_sessions:
        _agent_sessions[current_user["id"]].reset_memory()
        del _agent_sessions[current_user["id"]]
    
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
        
        # Limpar também a sessão do agente
        if current_user["id"] in _agent_sessions:
            _agent_sessions[current_user["id"]].reset_memory()
            del _agent_sessions[current_user["id"]]
        
        return SimpleResponse(message="Histórico de conversa limpo com sucesso!")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar histórico: {str(e)}")


@router.get(
    "/status",
    summary="Status do serviço de IA",
    description="Verifica o status do serviço de IA e se está configurado corretamente."
)
async def get_ai_status():
    """Retorna status do serviço de IA"""
    openai_configured = _is_openai_configured()
    
    return {
        "service": "suvinil-ai-chat",
        "status": "healthy",
        "ai_enabled": openai_configured,
        "model": "gpt-4o-mini" if openai_configured else "fallback",
        "features": {
            "semantic_search": openai_configured,
            "image_generation": openai_configured,
            "conversation_memory": True,
            "tool_usage": openai_configured,
        },
        "message": "IA totalmente funcional" if openai_configured else "Modo fallback - configure OPENAI_API_KEY para IA completa"
    }

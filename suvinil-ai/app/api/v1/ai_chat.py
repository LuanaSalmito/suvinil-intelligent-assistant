"""Endpoints de chat com IA"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.ai.agent_service import AgentService

router = APIRouter()

# Armazenar sessões de agentes por usuário (em produção, usar Redis)
_agent_sessions = {}


class ChatMessage(BaseModel):
    """Schema de mensagem do chat"""
    message: str
    reset_conversation: Optional[bool] = False


class ChatResponse(BaseModel):
    """Schema de resposta do chat"""
    response: str


def get_agent_service(
    user_id: int,
    db: Session,
    reset: bool = False,
) -> AgentService:
    """Obtém ou cria serviço de agente para o usuário"""
    if reset or user_id not in _agent_sessions:
        _agent_sessions[user_id] = AgentService(db)
    return _agent_sessions[user_id]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_message: ChatMessage,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Endpoint de chat com IA"""
    agent_service = get_agent_service(
        current_user["id"],
        db,
        reset=chat_message.reset_conversation,
    )
    
    if chat_message.reset_conversation:
        agent_service.reset_memory()
    
    try:
        response = agent_service.chat(chat_message.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no chat: {str(e)}")


@router.post("/chat/reset", response_model=ChatResponse)
async def reset_chat(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reseta conversa do chat"""
    if current_user["id"] in _agent_sessions:
        _agent_sessions[current_user["id"]].reset_memory()
        del _agent_sessions[current_user["id"]]
    
    return ChatResponse(response="Conversa resetada com sucesso.")

"""Endpoints de chat com IA"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_active_user, require_authenticated_user
from app.ai.agent_service import AgentService

router = APIRouter()
security_optional = HTTPBearer(auto_error=False)

# Armazenar sessões de agentes por usuário (em produção, usar Redis)
_agent_sessions = {}
_anonymous_sessions = {}  # Sessões para usuários não autenticados


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


def get_anonymous_agent_service(
    session_id: str,
    db: Session,
    reset: bool = False,
) -> AgentService:
    """Obtém ou cria serviço de agente para usuário anônimo"""
    if reset or session_id not in _anonymous_sessions:
        _anonymous_sessions[session_id] = AgentService(db)
    return _anonymous_sessions[session_id]


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """Obtém usuário se autenticado, None caso contrário"""
    if not credentials:
        return None
    try:
        # Decodificar token manualmente para obter usuário
        from app.core.security import decode_access_token
        from app.repositories.user_repository import UserRepository
        
        token = credentials.credentials
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = UserRepository.get_by_username(db, username)
        if user is None or not user.is_active:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        }
    except Exception:
        return None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_message: ChatMessage,
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint de chat com IA
    
    - Funciona com ou sem autenticação
    - Usuários autenticados (admin e user) têm sessão persistente
    - Usuários anônimos têm sessão temporária
    """
    try:
        if current_user and current_user.get("is_active"):
            # Usuário autenticado (admin ou user)
            agent_service = get_agent_service(
                current_user["id"],
                db,
                reset=chat_message.reset_conversation,
            )
        else:
            # Usuário anônimo - usar sessão baseada no timestamp
            # Em produção, usar cookies ou session ID do frontend
            import hashlib
            import time
            # Criar ID de sessão estável (pode ser melhorado com cookie)
            session_id = f"anonymous_{hashlib.md5(str(time.time() // 3600).encode()).hexdigest()[:8]}"
            agent_service = get_anonymous_agent_service(
                session_id,
                db,
                reset=chat_message.reset_conversation,
            )
        
        if chat_message.reset_conversation:
            agent_service.reset_memory()
        
        response = agent_service.chat(chat_message.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no chat: {str(e)}")


@router.post("/chat/reset", response_model=ChatResponse)
async def reset_chat(
    current_user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Reseta conversa do chat (funciona com ou sem autenticação)"""
    if current_user and current_user.get("is_active"):
        if current_user["id"] in _agent_sessions:
            _agent_sessions[current_user["id"]].reset_memory()
            del _agent_sessions[current_user["id"]]
    
    # Limpar sessões anônimas antigas também (opcional)
    # _anonymous_sessions.clear()
    
    return ChatResponse(response="Conversa resetada com sucesso.")

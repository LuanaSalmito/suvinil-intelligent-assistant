from sqlalchemy.orm import Session
from app.models.chat_message import ChatMessage


class AgentService:
    """
    Serviço de chat.
    NÃO decide nada.
    Apenas persiste conversa.
    """

    def save_message(
        self,
        db: Session,
        user_id: int,
        role: str,
        content: str
    ):
        message = ChatMessage(
            user_id=user_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()

    def respond(
        self,
        db: Session,
        user_id: int,
        user_message: str,
        response: str
    ):
        self.save_message(db, user_id, "user", user_message)
        self.save_message(db, user_id, "assistant", response)

        return {"response": response}

"""
Agente Orquestrador Multi-Especialistas Refatorado

Este agente coordena múltiplos especialistas, identifica tipo de superfície,
ambiente, cor e acabamento, e combina suas recomendações para fornecer
respostas precisas e consultivas.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import SystemMessage, HumanMessage

from app.ai.specialists import get_all_specialists, ColorAndFinishSpecialist
from app.ai.image_generator import ImageGenerator
from app.models.chat_message import ChatMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = """Você é um Assistente Inteligente Suvinil, especialista em recomendações de tintas.

Coordena uma equipe de especialistas:
- Ambientes Internos (quartos, salas, banheiros)
- Ambientes Externos (fachadas, muros, varandas)
- Cores e Acabamentos (harmonização e psicologia das cores)
- Durabilidade (madeira, metal, resistência)

ESTILO DE RESPOSTA:
- Consultivo e profissional
- Respostas diretas e concisas
- Sugira APENAS 1 produto por vez
- Explique brevemente POR QUE é a melhor escolha
- Pergunta de follow-up curta se necessário
"""

class OrchestratorAgent:
    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        
        # LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            max_tokens=400,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Memória de conversa
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10
        )
        if user_id:
            self._load_history_from_db()
        
        # Especialistas
        self.specialists = get_all_specialists(db)
        
        # Gerador de imagens
        try:
            self.image_generator = ImageGenerator()
        except Exception as e:
            logger.warning(f"Image generator não disponível: {e}")
            self.image_generator = None
        
        self.last_execution_metadata: Dict[str, Any] = {}
        logger.info(f"OrchestratorAgent inicializado com {len(self.specialists)} especialistas")
    
    def _load_history_from_db(self):
        """Carrega histórico de mensagens do banco"""
        try:
            messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.user_id == self.user_id)
                .order_by(ChatMessage.created_at.asc())
                .limit(20)
                .all()
            )
            for msg in messages:
                if msg.role == "user":
                    self.memory.chat_memory.add_user_message(msg.content)
                elif msg.role == "assistant":
                    self.memory.chat_memory.add_ai_message(msg.content)
            logger.info(f"Histórico carregado: {len(messages)} mensagens")
        except Exception as e:
            logger.warning(f"Erro ao carregar histórico: {e}")
    
    def _save_message_to_db(self, role: str, content: str):
        if not self.user_id:
            return
        try:
            message = ChatMessage(
                user_id=self.user_id,
                role=role,
                content=content,
                created_at=datetime.utcnow()
            )
            self.db.add(message)
            self.db.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
            self.db.rollback()
    
    def _extract_context(self, message: str) -> Dict[str, Any]:
        """Extrai contexto completo: cor, acabamento, ambiente e superfície"""
        message_lower = message.lower()

        # ===== Cor =====
        color_map = {
            "azul": ["azul", "blue"],
            "vermelho": ["vermelho", "red"],
            "verde": ["verde", "green"],
            "amarelo": ["amarelo", "yellow"],
            "branco": ["branco", "white"],
            "cinza": ["cinza", "gray", "grey"],
            "rosa": ["rosa", "pink"],
            "roxo": ["roxo", "violeta", "lilás", "roxa"],
            "laranja": ["laranja", "orange"],
            "bege": ["bege", "nude"],
        }
        color = None
        color_from_message = None
        for key, variations in color_map.items():
            if any(var in message_lower for var in variations):
                color = key
                color_from_message = key
                break

        # ===== Acabamento =====
        finish_type = None
        if "fosco" in message_lower:
            finish_type = "fosco"
        elif "brilhante" in message_lower:
            finish_type = "brilhante"
        elif "semi-brilhante" in message_lower or "semi brilhante" in message_lower:
            finish_type = "semi-brilhante"
        elif "acetinado" in message_lower:
            finish_type = "acetinado"

        # ===== Ambiente =====
        environment = None
        room_type = None
        if any(word in message_lower for word in ["quarto", "dormitório"]):
            environment = "interno"
            room_type = "quarto"
        elif any(word in message_lower for word in ["sala", "living"]):
            environment = "interno"
            room_type = "sala"
        elif any(word in message_lower for word in ["escritório", "home office"]):
            environment = "interno"
            room_type = "escritório"
        elif any(word in message_lower for word in ["banheiro", "lavabo"]):
            environment = "interno"
            room_type = "banheiro"
        elif any(word in message_lower for word in ["cozinha"]):
            environment = "interno"
            room_type = "cozinha"
        elif any(word in message_lower for word in ["fachada", "externo", "muro", "varanda"]):
            environment = "externo"
            room_type = "fachada"

        # ===== Superfície =====
        surface_type = None
        if "madeira" in message_lower:
            surface_type = "madeira"
        elif "metal" in message_lower:
            surface_type = "metal"
        elif "azulejo" in message_lower or "cerâmica" in message_lower:
            surface_type = "azulejo"
        elif "paredes" in message_lower or "gesso" in message_lower:
            surface_type = "parede"

        # ===== Visualização =====
        wants_visualization = any(word in message_lower for word in [
            "mostra", "mostrar", "ver", "visualizar", "imagem", "como ficaria",
            "pode mostrar", "gostaria de ver", "quero ver", "me mostra"
        ])

        return {
            "color": color,
            "finish_type": finish_type,
            "environment": environment,
            "room_type": room_type,
            "surface_type": surface_type,
            "wants_visualization": wants_visualization,
            "original_message": message,
            "is_new_query": True,
            "color_from_message": color_from_message
        }

    def _select_specialists(self, message: str, context: Dict[str, Any]) -> List[Any]:
        selected = [s for s in self.specialists if s.can_handle(message, context)]
        if not selected:
            selected = [s for s in self.specialists if isinstance(s, ColorAndFinishSpecialist)]
        return selected

    def _consult_specialists(self, message: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        specialists = self._select_specialists(message, context)
        results = []
        for specialist in specialists:
            try:
                res = specialist.consult(message, context)
                results.append(res)
            except Exception as e:
                logger.error(f"Erro ao consultar {specialist.name}: {e}")
        return results

    def _generate_response(
        self, message: str, context: Dict[str, Any], specialist_results: List[Dict[str, Any]]
    ) -> str:
        if not specialist_results or all(len(r.get("recommendations", [])) == 0 for r in specialist_results):
            missing = []
            if not context.get("environment"):
                missing.append("interno ou externo")
            if not context.get("surface_type"):
                missing.append("tipo de superfície (madeira, metal, azulejo)")
            if not context.get("finish_type"):
                missing.append("acabamento (fosco, acetinado, brilhante)")
            if missing:
                return f"Me conta mais sobre o que você precisa: {', '.join(missing)}?"
            return "Desculpe, não consegui encontrar recomendações. Pode me dar mais detalhes?"

        # Melhor recomendação
        all_recs = []
        for r in specialist_results:
            all_recs.extend(r.get("recommendations", []))
        best = all_recs[0]

        features_text = ", ".join(best.get('match_reasons', [])[:2]) or best.get('features', 'Alta qualidade')
        response = (
            f"Consultei nossos especialistas. Recomendo a {best['name']} "
            f"para {context.get('surface_type', 'a superfície desejada')}, "
            f"acabamento {best['finish']}, {features_text}. "
            f"R$ {best.get('price', 0):.2f}. "
        )
        if context.get("wants_visualization") and self.image_generator:
            response += "\nPosso gerar uma visualização mostrando como ficaria. Quer ver?"
        return response

    async def chat(self, message: str) -> Dict[str, Any]:
        start_time = datetime.utcnow()
        context = self._extract_context(message)
        specialist_results = self._consult_specialists(message, context)
        response_text = self._generate_response(message, context, specialist_results)

        # Salvar na memória e banco
        self.memory.chat_memory.add_user_message(message)
        self.memory.chat_memory.add_ai_message(response_text)
        self._save_message_to_db("user", message)
        self._save_message_to_db("assistant", response_text)

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds() * 1000
        specialists_used = [
            {"specialist": r["specialist"], "confidence": r.get("confidence", 0)}
            for r in specialist_results
        ]

        self.last_execution_metadata = {
            "specialists_consulted": specialists_used,
            "total_recommendations": sum(len(r.get("recommendations", [])) for r in specialist_results),
            "execution_time_ms": execution_time,
            "context_extracted": context
        }

        return {
            "response": response_text,
            "specialists_consulted": specialists_used,
            "metadata": self.last_execution_metadata
        }

    def reset_memory(self):
        self.memory.clear()
    
    def get_conversation_summary(self) -> str:
        messages = self.memory.chat_memory.messages
        return f"Conversa com {len(messages)} mensagens. Especialistas disponíveis: {len(self.specialists)}."

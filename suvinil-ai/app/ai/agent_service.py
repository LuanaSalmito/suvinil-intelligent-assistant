"""
Agente Inteligente Especialista em Tintas Suvinil

Este módulo implementa um agente consultor de tintas, capaz de:
- Entender a necessidade do usuário
- Buscar produtos adequados
- Fornecer explicações claras e humanas
- Manter o contexto da conversa
- Gerar recomendações proativas e personalizadas
"""

import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.memory import ConversationBufferWindowMemory

from app.repositories.paint_repository import PaintRepository
from app.models.chat_message import ChatMessage
from app.models.paint import Environment, FinishType, PaintLine
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Prompt do agente
# -------------------------------------------------------------------
SYSTEM_PROMPT = """
Você é um consultor especializado em tintas Suvinil.
Seu objetivo é ajudar o usuário a escolher a tinta ideal com explicações claras e amigáveis.
Pense como se estivesse falando com um cliente pessoalmente. Seja acolhedor, humano e profissional.

- Analise o ambiente, tipo de superfície, cores e características desejadas.
- Explique por que determinada tinta é adequada.
- Sugira alternativas e faça perguntas de acompanhamento quando necessário.
- Se não souber algo, diga honestamente e ofereça opções seguras.
"""

# -------------------------------------------------------------------
# Classe principal do agente
# -------------------------------------------------------------------
class AgentService:
    """
    Agente de conversa para recomendações de tintas Suvinil.
    Mantém memória, histórico no banco e utiliza ferramentas de busca.
    """

    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id

        # LLM configurado para respostas naturais e humanas
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.8,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        # Memória de conversa com janela de 10 mensagens
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10
        )

        # Carregar histórico se houver user_id
        if user_id:
            self._load_history_from_db()

        # Criar agente com ferramentas
        self.agent = self._create_agent()

        # Metadados da última execução
        self.last_execution_metadata: Dict[str, Any] = {}

        logger.info(f"AgentService inicializado para user_id={user_id}")

    # -------------------------------------------------------------------
    # Histórico
    # -------------------------------------------------------------------
    def _load_history_from_db(self):
        """Carrega histórico de mensagens do banco de dados"""
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
        """Salva mensagem no banco"""
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

    # -------------------------------------------------------------------
    # Ferramentas
    # -------------------------------------------------------------------
    def _create_tools(self) -> List[Tool]:
        """Ferramentas disponíveis para o agente"""

        # 1. Busca de tintas por características ou cores
        def search_paints(query: str) -> str:
            logger.info(f"[TOOL] search_paints: query='{query}'")
            paints = PaintRepository.get_all(self.db, limit=50)
            if not paints:
                return "Não encontrei tintas no catálogo no momento."

            query_lower = query.lower()
            scored = []
            for paint in paints:
                score = 0
                text = f"{paint.name} {paint.color_name or ''} {paint.features or ''} {paint.description or ''}".lower()
                for kw in query_lower.split():
                    if kw in text:
                        score += 1
                if score > 0:
                    scored.append((paint, score))

            scored.sort(key=lambda x: x[1], reverse=True)
            top_paints = [p for p, _ in scored[:5]] if scored else paints[:5]

            response = "Aqui estão algumas tintas que podem atender ao que você procura:\n"
            for p in top_paints:
                features = ", ".join([f.strip() for f in (p.features.split(",") if p.features else [])[:4]])
                response += f"- {p.name} ({p.color_name or 'Variações de cor'})\n"
                response += f"  Linha: {p.line.value}, Acabamento: {p.finish_type.value}\n"
                if features:
                    response += f"  Características: {features}\n"
                if p.price:
                    response += f"  Preço aproximado: R$ {p.price:.2f}\n"
                response += "\n"
            return response

        # 2. Filtrar por ambiente
        def filter_by_environment(environment: str) -> str:
            env_map = {
                "interno": Environment.INTERIOR,
                "interior": Environment.INTERIOR,
                "externo": Environment.EXTERIOR,
                "exterior": Environment.EXTERIOR,
                "ambos": Environment.BOTH
            }
            env = env_map.get(environment.lower())
            if not env:
                return f"Não reconheci o ambiente '{environment}'. Use interno, externo ou ambos."

            paints = PaintRepository.get_all(self.db, environment=env, limit=10)
            if not paints:
                return f"Não encontrei tintas para ambiente {environment}."

            response = f"Tintas recomendadas para ambiente {environment}:\n"
            for p in paints:
                features = ", ".join([f.strip() for f in (p.features.split(",") if p.features else [])[:3]])
                response += f"- {p.name} ({p.color_name or 'Várias cores'})\n"
                response += f"  Acabamento: {p.finish_type.value}, Linha: {p.line.value}\n"
                if features:
                    response += f"  Características: {features}\n"
                if p.price:
                    response += f"  Preço: R$ {p.price:.2f}\n"
            return response

        # 3. Detalhes de uma tinta específica
        def get_paint_details(paint_id: str) -> str:
            try:
                pid = int(paint_id)
                paint = PaintRepository.get_by_id(self.db, pid)
                if not paint or not paint.is_active:
                    return f"Tinta com ID {paint_id} não encontrada."

                features = ", ".join([f.strip() for f in (paint.features.split(",") if paint.features else [])])
                resp = f"Detalhes da tinta {paint.name}:\n"
                resp += f"- Cor: {paint.color_name or paint.color or 'Não especificada'}\n"
                resp += f"- Linha: {paint.line.value}, Acabamento: {paint.finish_type.value}\n"
                resp += f"- Superfície: {paint.surface_type or 'Múltiplas'}\n"
                resp += f"- Ambiente: {paint.environment.value}\n"
                if features:
                    resp += f"- Características: {features}\n"
                if paint.description:
                    resp += f"- Descrição: {paint.description}\n"
                if paint.price:
                    resp += f"- Preço: R$ {paint.price:.2f}\n"
                return resp
            except Exception as e:
                return f"Erro ao buscar detalhes da tinta: {str(e)}"

        # 4. Listar todas as tintas
        def list_all_paints(_: str = "") -> str:
            paints = PaintRepository.get_all(self.db, limit=50)
            if not paints:
                return "Nenhuma tinta disponível no catálogo."

            response = f"Catálogo de Tintas Suvinil ({len(paints)} produtos):\n"
            by_line = {}
            for p in paints:
                by_line.setdefault(p.line.value, []).append(p)

            for line, items in by_line.items():
                response += f"\nLinha {line}:\n"
                for p in items[:10]:
                    response += f"- {p.name} ({p.color_name or 'Várias cores'})\n"
                if len(items) > 10:
                    response += f"... e mais {len(items) - 10} produtos\n"

            return response

        tools = [
            Tool(name="search_paints", func=search_paints,
                 description="Buscar tintas por cores, características ou ambiente"),
            Tool(name="filter_paints_by_environment", func=filter_by_environment,
                 description="Filtrar tintas por ambiente: interno, externo ou ambos"),
            Tool(name="get_paint_details", func=get_paint_details,
                 description="Obter detalhes completos de uma tinta por ID"),
            Tool(name="list_all_paints", func=list_all_paints,
                 description="Listar todas as tintas disponíveis no catálogo")
        ]

        return tools

    # -------------------------------------------------------------------
    # Criação do agente
    # -------------------------------------------------------------------
    def _create_agent(self) -> AgentExecutor:
        tools = self._create_tools()

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = create_openai_tools_agent(self.llm, tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=True
        )

    # -------------------------------------------------------------------
    # Conversa
    # -------------------------------------------------------------------
    def chat(self, message: str) -> Dict[str, Any]:
        logger.info(f"[CHAT] Mensagem recebida: '{message[:50]}...'")

        try:
            chat_history = self.memory.chat_memory.messages
            input_dict = {"input": message, "chat_history": chat_history if chat_history else []}

            start_time = datetime.utcnow()
            result = self.agent.invoke(input_dict)
            end_time = datetime.utcnow()

            response_text = result.get("output", "Desculpe, não consegui entender completamente.")
            tools_used, paints_mentioned = [], []

            for step in result.get("intermediate_steps", []):
                try:
                    if len(step) >= 2:
                        action, observation = step[0], step[1]
                        tool_name = getattr(action, 'tool', str(action))
                        tool_input = getattr(action, 'tool_input', '')
                        tools_used.append({"tool": tool_name, "input": str(tool_input)})
                        ids = re.findall(r'ID:\s*(\d+)', str(observation))
                        paints_mentioned.extend([int(i) for i in ids])
                except Exception:
                    continue

            self.memory.chat_memory.add_user_message(message)
            self.memory.chat_memory.add_ai_message(response_text)
            self._save_message_to_db("user", message)
            self._save_message_to_db("assistant", response_text)

            execution_time = (end_time - start_time).total_seconds() * 1000
            self.last_execution_metadata = {
                "tools_used": tools_used,
                "paints_mentioned": list(set(paints_mentioned)),
                "execution_time_ms": execution_time,
                "intermediate_steps_count": len(result.get("intermediate_steps", []))
            }

            return {
                "response": response_text,
                "tools_used": tools_used,
                "paints_mentioned": list(set(paints_mentioned)),
                "metadata": self.last_execution_metadata
            }

        except Exception as e:
            logger.error(f"[CHAT] Erro: {e}", exc_info=True)
            return {
                "response": "Desculpe, houve um problema ao processar sua mensagem.",
                "tools_used": [],
                "paints_mentioned": [],
                "metadata": {"error": str(e)}
            }

    # -------------------------------------------------------------------
    # Reset e resumo
    # -------------------------------------------------------------------
    def reset_memory(self):
        logger.info(f"[MEMORY] Resetando memória para user_id={self.user_id}")
        self.memory.clear()
        self.agent = self._create_agent()

    def get_conversation_summary(self) -> str:
        messages = self.memory.chat_memory.messages
        if not messages:
            return "Nenhuma conversa iniciada."
        return f"Conversa com {len(messages)} mensagens."


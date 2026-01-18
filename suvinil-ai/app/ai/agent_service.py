from typing import List, Optional
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from app.ai.rag_service import RAGService
from app.repositories.paint_repository import PaintRepository
from app.core.config import settings
import json


class AgentService:
  
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService(db)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Cria ferramentas disponíveis para o agente"""
        
        def search_paints_tool(query: str) -> str:
            """Busca tintas relevantes baseado na consulta do usuário"""
            paints = self.rag_service.search_paints(query, k=5)
            if not paints:
                return "Nenhuma tinta encontrada para essa consulta."
            
            result = "Tintas encontradas:\n"
            for paint in paints:
                result += f"\n- {paint['name']}"
                result += f"\n  Cor: {paint['color']}"
                result += f"\n  Ambiente: {paint['environment']}"
                result += f"\n  Acabamento: {paint['finish_type']}"
                result += f"\n  Linha: {paint['line']}"
                result += f"\n  {paint['content']}\n"
            
            return result
        
        def get_paint_details_tool(paint_id: str) -> str:
            """Obtém detalhes completos de uma tinta específica"""
            try:
                paint = PaintRepository.get_by_id(self.db, int(paint_id))
                if not paint or not paint.is_active:
                    return f"Tinta com ID {paint_id} não encontrada."
                
                features_list = paint.features.split(",") if paint.features else []
                result = f"""
Detalhes da tinta {paint.name}:
- ID: {paint.id}
- Cor: {paint.color_name or paint.color or "Não especificada"}
- Tipo de superfície: {paint.surface_type or "Não especificado"}
- Ambiente: {paint.environment.value}
- Acabamento: {paint.finish_type.value}
- Linha: {paint.line.value}
- Features: {", ".join([f.strip() for f in features_list]) if features_list else "Nenhuma"}
- Descrição: {paint.description or "Não disponível"}
- Preço: R$ {paint.price or "Não disponível"}
                """.strip()
                
                return result
            except Exception as e:
                return f"Erro ao buscar detalhes da tinta: {str(e)}"
        
        def list_all_paints_tool() -> str:
            """Lista todas as tintas disponíveis"""
            paints = PaintRepository.get_all(self.db, skip=0, limit=100)
            if not paints:
                return "Nenhuma tinta disponível no catálogo."
            
            result = "Tintas disponíveis no catálogo:\n"
            for paint in paints:
                result += f"\n- {paint.name} (ID: {paint.id})"
                result += f" - {paint.color_name or paint.color or 'Cor não especificada'}"
                result += f" - {paint.environment.value}"
            
            return result
        
        tools = [
            Tool(
                name="search_paints",
                func=search_paints_tool,
                description="""Busca tintas no catálogo baseado em critérios como:
                - Tipo de ambiente (interno/externo)
                - Características (lavável, anti-mofo, sem odor, etc.)
                - Cor desejada
                - Tipo de superfície (parede, madeira, etc.)
                - Tipo de acabamento (fosco, acetinado, brilhante)
                Use quando o usuário perguntar sobre recomendações de tintas.""",
            ),
            Tool(
                name="get_paint_details",
                func=get_paint_details_tool,
                description="Obtém informações detalhadas de uma tinta específica usando seu ID. Use quando precisar de mais detalhes sobre uma tinta mencionada.",
            ),
            Tool(
                name="list_all_paints",
                func=list_all_paints_tool,
                description="Lista todas as tintas disponíveis no catálogo. Use quando o usuário pedir para ver todas as opções ou o catálogo completo.",
            ),
        ]
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Cria agente com ferramentas"""
        tools = self._create_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente virtual especialista em tintas Suvinil.
Seu papel é ajudar pessoas a escolherem o produto ideal baseado em suas necessidades, preferências e contexto.

Quando o usuário fizer uma pergunta:
1. Use as ferramentas disponíveis para buscar informações relevantes no catálogo
2. Analise os resultados e faça recomendações personalizadas
3. Explique claramente porque aquela tinta é adequada
4. Seja amigável, profissional e prestativo
5. Se não encontrar algo específico, seja honesto e sugira alternativas quando possível

Sempre que mencionar uma tinta, mencione seu nome completo e características principais."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
        )
        
        return agent_executor
    
    def chat(self, message: str) -> str:
        """Processa mensagem do usuário e retorna resposta do agente"""
        try:
            # Obter histórico da memória
            chat_history = self.memory.chat_memory.messages
            
            # Preparar contexto
            input_dict = {"input": message}
            if chat_history:
                input_dict["chat_history"] = chat_history
            
            response = self.agent.invoke(input_dict)
            
            # Salvar mensagens na memória
            self.memory.chat_memory.add_user_message(message)
            self.memory.chat_memory.add_ai_message(response.get("output", ""))
            
            return response.get("output", "Desculpe, não consegui processar sua mensagem.")
        except Exception as e:
            return f"Erro ao processar mensagem: {str(e)}"
    
    def reset_memory(self):
        """Reseta memória da conversa"""
        self.memory.clear()
        self.agent = self._create_agent()

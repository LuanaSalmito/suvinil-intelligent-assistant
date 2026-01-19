"""
Agente Inteligente Especialista em Tintas Suvinil - Conversa Fluida e Humana
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
from langchain_core.messages import SystemMessage, HumanMessage

from app.repositories.paint_repository import PaintRepository
from app.ai.rag_service import RAGService
from app.models.chat_message import ChatMessage
from app.models.paint import Environment, FinishType, PaintLine
from app.core.config import settings

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Prompt do agente - Conversacional e humano
# -------------------------------------------------------------------
SYSTEM_PROMPT = """
Você é um consultor especializado em tintas Suvinil. Seja direto, objetivo e consultivo.

📌 ESTILO DE RESPOSTA (OBRIGATÓRIO):
- Respostas curtas e diretas (máximo 3-4 frases)
- Sugira APENAS 1 produto por vez, não liste múltiplas opções
- Inclua apenas: nome do produto, cor, 2-3 características principais
- Termine com UMA pergunta de follow-up curta
- NÃO use emojis
- NÃO use analogias ou humor
- NÃO faça parágrafos longos

📌 REGRA CRÍTICA DE COR (OBRIGATÓRIO):
- Quando o usuário mencionar uma COR ESPECÍFICA (azul, verde, vermelho, etc.), use a ferramenta search_paints_by_color
- NUNCA sugira Branco quando o usuário pedir outra cor
- Se não encontrar a cor exata, informe que não tem e use list_available_colors para mostrar as cores disponíveis
- A COR mencionada pelo usuário é MAIS IMPORTANTE que qualquer outra característica

📌 REGRAS DE CONTEXTO (CRÍTICO - MAIS IMPORTANTE):
- SEMPRE considere TODO o histórico da conversa ao responder
- Se o usuário já mencionou o ambiente (quarto, sala, fachada, etc.), MANTENHA esse contexto nas próximas respostas
- Se o usuário já mencionou características (para filho, bebê, adolescente, etc.), LEMBRE-SE disso
- Quando o usuário pedir mudanças (cor diferente, acabamento diferente), mantenha TUDO do contexto anterior
- NUNCA pergunte novamente sobre informações que o usuário já forneceu
- Exemplo CRÍTICO:
  Usuário: "quero pintar o quarto do meu filho de azul"
  Usuário: "na verdade, prefiro verde"
  IA deve lembrar: QUARTO + FILHO + VERDE (não perguntar "é para interno ou externo?")
- SEMPRE mencione o contexto anterior na resposta para mostrar que você lembrou

📌 REGRAS DE USO DAS FERRAMENTAS:
- COR MENCIONADA → Use search_paints_by_color("cor")
- "Quais cores tem?" → Use list_available_colors()
- Busca geral sem cor → Use rag_search_paints("query")
- Nunca invente nomes de tintas ou cores
- SEMPRE use uma ferramenta antes de recomendar um produto

EXEMPLOS DE RESPOSTAS CORRETAS:

Usuário: "Quero pintar meu quarto, fácil de limpar e sem cheiro"
IA: [Usa rag_search_paints: "quarto lavável sem cheiro"]
IA: "Para quartos, recomendo a Suvinil Fosco Branco 12, lavável e sem odor, acabamento fosco. R$ 89.90. Você prefere acabamento fosco ou acetinado?"

Usuário: "quero pintar o quarto do meu filho em um tom de azul"
IA: [Usa search_paints_by_color: "azul"]
IA: "Para quarto infantil em azul, recomendo a Suvinil Brilhante Azul 5 - Azul, alta cobertura e resistente, acabamento brilhante. R$ 115.06. Que tal?"

Usuário: "fosco, mas acho que verde é uma boa também"
IA: [LEMBRA: quarto + filho, Usa search_paints_by_color: "verde"]
IA: "Para o quarto do seu filho em verde com acabamento fosco, recomendo a Suvinil Fosco Verde 40 - Verde, resistente e lavável. R$ 113.37. Essa opção te agrada?"

Usuário: "Quais cores vocês tem?"
IA: [Usa list_available_colors]
IA: "Temos várias cores disponíveis: Azul (15 tintas), Vermelho (15), Branco (11), Verde (10), Laranja (10), Rosa (9)... Qual cor você prefere?"

EXEMPLO DE ERRO (NÃO FAÇA ISSO):

Usuário: "quero em azul"
IA: [Usa rag_search_paints sem verificar cor]
IA: "Recomendo Suvinil Toque de Seda - Branco Neve..." ❌ ERRADO!

Correto:
Usuário: "quero em azul"  
IA: [Usa search_paints_by_color: "azul"]
IA: "Para azul, recomendo a Suvinil Fosco Azul 16 - Azul, acabamento fosco. R$ 67.80" ✓ CORRETO!
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
        self.rag_service = RAGService(db)

        # LLM configurado para respostas diretas e objetivas
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.5,  # Temperatura baixa para respostas consistentes e diretas
            max_tokens=350,   # Limite reduzido para forçar respostas concisas
            openai_api_key=settings.OPENAI_API_KEY,
        )

        # Memória de conversa (últimas 10 mensagens)
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10
        )

        if user_id:
            self._load_history_from_db()

        # Criar agente com ferramentas
        self.agent = self._create_agent()
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

        def _infer_environment(query_lower: str) -> Optional[str]:
            if any(term in query_lower for term in ["interno", "interior", "quarto", "sala", "escritório"]):
                return Environment.INTERIOR.value
            if any(term in query_lower for term in ["externo", "exterior", "fachada", "muro", "varanda"]):
                return Environment.EXTERIOR.value
            if any(term in query_lower for term in ["ambos", "interno e externo", "duplo uso"]):
                return Environment.BOTH.value
            return None

        def _infer_finish(query_lower: str) -> Optional[str]:
            if "fosco" in query_lower:
                return FinishType.FOSCO.value
            if "acetinado" in query_lower:
                return FinishType.ACETINADO.value
            if "semi-brilhante" in query_lower or "semi brilhante" in query_lower:
                return FinishType.SEMI_BRILHANTE.value
            if "brilhante" in query_lower:
                return FinishType.BRILHANTE.value
            return None

        def _infer_color(query_lower: str) -> Optional[str]:
            """Detecta a cor mencionada na query"""
            color_map = {
                "azul": ["azul", "blue"],
                "vermelho": ["vermelho", "red", "vermelhao"],
                "verde": ["verde", "green"],
                "amarelo": ["amarelo", "yellow"],
                "branco": ["branco", "white"],
                "preto": ["preto", "black"],
                "cinza": ["cinza", "gray", "grey"],
                "rosa": ["rosa", "pink"],
                "roxo": ["roxo", "violeta", "roxo", "lilas", "lilás"],
                "laranja": ["laranja", "orange"],
                "marrom": ["marrom", "brown"],
                "bege": ["bege", "nude", "areia"],
                "turquesa": ["turquesa", "turquoise"],
            }
            
            for color_key, variations in color_map.items():
                if any(var in query_lower for var in variations):
                    return color_key
            return None

        def _format_rag_results(results: List[Dict[str, Any]], requested_color: Optional[str] = None, include_intro: bool = True) -> str:
            if not results:
                return "Não encontrei tintas no catálogo para essa busca."
            
            # Se uma cor foi solicitada, filtrar apenas resultados com essa cor
            if requested_color:
                filtered_results = []
                for r in results:
                    color_in_result = (r.get("color") or "").lower()
                    color_name_in_result = (r.get("color_name") or "").lower()
                    
                    # Verificar se a cor solicitada está presente
                    if requested_color in color_in_result or requested_color in color_name_in_result:
                        filtered_results.append(r)
                
                # Se encontrou tintas com a cor solicitada, usar essas
                if filtered_results:
                    results = filtered_results
                else:
                    # Se não encontrou, avisar
                    return f"Não encontrei tintas na cor {requested_color} no catálogo. Temos outras cores disponíveis se você quiser explorar."
            
            # Retorna apenas o primeiro resultado com informações diretas
            p = results[0]
            features = ", ".join([f.strip() for f in (p.get("features", "").split(",") if p.get("features") else [])[:3]])
            response = f"{p.get('name')} - {p.get('color') or 'cor variável'}. "
            response += f"Linha {p.get('line')}, acabamento {p.get('finish_type')}. "
            if features:
                response += f"Características: {features}. "
            if p.get("price"):
                response += f"Preço: R$ {p.get('price'):.2f}."
            return response

        # Busca direta no banco (funciona sem OpenAI)
        def search_paints_by_color(color: str) -> str:
            """
            Busca tintas diretamente no banco de dados por cor.
            Funciona mesmo sem OpenAI API.
            MANTÉM CONTEXTO da conversa anterior.
            """
            color_lower = color.lower()
            
            # Inferir TUDO do histórico para manter contexto completo
            chat_history = self.memory.chat_memory.messages
            recent_messages = chat_history[-6:] if len(chat_history) > 0 else []
            history_text = " ".join([msg.content.lower() for msg in recent_messages if hasattr(msg, 'content')])
            
            env = _infer_environment(history_text)
            finish = _infer_finish(history_text)
            
            # Extrair contexto adicional do histórico
            context_parts = []
            if "quarto" in history_text:
                context_parts.append("quarto")
            elif "sala" in history_text:
                context_parts.append("sala")
            elif "banheiro" in history_text:
                context_parts.append("banheiro")
            elif "cozinha" in history_text:
                context_parts.append("cozinha")
            
            # Detectar público-alvo
            age_context = None
            if "filho" in history_text or "filha" in history_text or "criança" in history_text:
                age_context = "infantil"
            elif "bebê" in history_text or "bebe" in history_text:
                age_context = "bebê"
            elif "adolescente" in history_text:
                age_context = "adolescente"
            
            # Buscar no banco
            paints = PaintRepository.find_by_color(
                self.db,
                color=color_lower,
                environment=env,
                finish_type=finish,
                limit=10
            )
            
            if not paints:
                # Listar cores disponíveis
                available_colors = PaintRepository.get_available_colors(self.db)
                colors_list = ", ".join([c["color_display"] for c in available_colors[:5]])
                context_desc = f" para {' '.join(context_parts)}" if context_parts else ""
                return f"Não encontrei tintas na cor {color}{context_desc}. Cores disponíveis: {colors_list}."
            
            # Formatar resultado COM CONTEXTO
            paint = paints[0]
            features = ", ".join([f.strip() for f in (paint.features.split(",") if paint.features else [])[:2]])
            
            # Construir resposta mantendo contexto
            response = f"Para"
            if context_parts:
                response += f" {' '.join(context_parts)}"
                if age_context:
                    response += f" {age_context}"
            else:
                response += " sua necessidade"
            
            response += f" na cor {color_lower}, recomendo {paint.name} - {paint.color_name}. "
            if features:
                response += f"{features}, "
            response += f"acabamento {paint.finish_type.value}"
            if paint.price:
                response += f". R$ {paint.price:.2f}"
            response += f". ID: {paint.id}"
            
            logger.info(f"[SEARCH] Encontrada tinta: {paint.name} (ID: {paint.id}) com contexto: {context_parts}, {age_context}")
            return response

        # Busca semântica RAG (com fallback para banco direto)
        def rag_search_paints(query: str) -> str:
            """
            Busca tintas considerando o contexto da conversa.
            Usa RAG se disponível, caso contrário busca no banco direto.
            """
            query_lower = query.lower()
            
            # Tentar inferir do query atual
            env = _infer_environment(query_lower)
            finish = _infer_finish(query_lower)
            requested_color = _infer_color(query_lower)
            
            # Se não encontrou no query atual, buscar no histórico recente
            if not env or not finish or not requested_color:
                chat_history = self.memory.chat_memory.messages
                recent_messages = chat_history[-4:] if len(chat_history) > 0 else []
                history_text = " ".join([msg.content.lower() for msg in recent_messages if hasattr(msg, 'content')])
                
                if not env:
                    env = _infer_environment(history_text)
                if not finish:
                    finish = _infer_finish(history_text)
                if not requested_color:
                    requested_color = _infer_color(history_text)
                
                # Adicionar contexto relevante ao query
                if history_text:
                    if "quarto" in history_text and "quarto" not in query_lower:
                        query = f"quarto {query}"
                    elif "sala" in history_text and "sala" not in query_lower:
                        query = f"sala {query}"
                    elif "banheiro" in history_text and "banheiro" not in query_lower:
                        query = f"banheiro {query}"
                    
                    if any(term in history_text for term in ["filho", "criança", "infantil", "bebê"]) and "infantil" not in query_lower:
                        query = f"infantil {query}"
            
            # Se cor foi detectada, usar busca direta no banco (mais confiável e rápido)
            if requested_color:
                logger.info(f"[RAG] Cor detectada: {requested_color}, usando busca direta no banco")
                return search_paints_by_color(requested_color)
            
            # Tentar busca RAG semântica (para consultas sem cor específica)
            try:
                logger.info(f"[RAG] Tentando busca semântica para: '{query}'")
                results = self.rag_service.search_paints(
                    query=query,
                    k=10,
                    filter_environment=env,
                    filter_finish=finish,
                )
                if results:
                    logger.info(f"[RAG] Busca semântica retornou {len(results)} resultados")
                    return _format_rag_results(results, requested_color=requested_color)
                else:
                    logger.info("[RAG] Busca semântica não retornou resultados")
            except Exception as e:
                logger.warning(f"[RAG] Erro na busca semântica, usando banco direto: {e}")
            
            # Fallback: busca no banco direto
            paints = PaintRepository.search(
                self.db,
                query=query,
                environment=env,
                finish_type=finish,
                limit=5
            )
            
            if not paints:
                return "Não encontrei tintas para essa busca. Me diga mais detalhes como cor e ambiente."
            
            paint = paints[0]
            features = ", ".join([f.strip() for f in (paint.features.split(",") if paint.features else [])[:2]])
            response = f"{paint.name} - {paint.color_name}. "
            if features:
                response += f"{features}, "
            response += f"acabamento {paint.finish_type.value}"
            if paint.price:
                response += f". R$ {paint.price:.2f}"
            return response

        # Listar cores disponíveis
        def list_available_colors(_: str = "") -> str:
            """Lista todas as cores disponíveis no catálogo"""
            colors = PaintRepository.get_available_colors(self.db)
            if not colors:
                return "Nenhuma cor disponível no catálogo."
            
            response = "Cores disponíveis no catálogo Suvinil:\n"
            for color_info in colors:
                response += f"- {color_info['color_display']}: {color_info['count']} tintas\n"
            return response
        
        # Listar catálogo completo
        def list_all_paints(_: str = "") -> str:
            paints = PaintRepository.get_all(self.db, limit=50)
            if not paints:
                return "Nenhuma tinta disponível no catálogo."
            response = f"Catálogo de Tintas Suvinil ({len(paints)} produtos):\n"
            for p in paints[:10]:
                response += f"- {p.name} - {p.color_name or 'Várias cores'} | R$ {p.price:.2f}\n"
            if len(paints) > 10:
                response += f"... e mais {len(paints) - 10} produtos\n"
            return response

        tools = [
            Tool(
                name="search_paints_by_color",
                func=search_paints_by_color,
                description="Busca tintas por cor específica no banco de dados. Use quando o usuário mencionar uma cor (azul, verde, vermelho, etc.). Exemplo: search_paints_by_color('azul')"
            ),
            Tool(
                name="rag_search_paints",
                func=rag_search_paints,
                description="Busca tintas por características gerais (ambiente, acabamento, features). Use para buscas complexas sem cor específica."
            ),
            Tool(
                name="list_available_colors",
                func=list_available_colors,
                description="Lista todas as cores disponíveis no catálogo com quantidade de tintas. Use quando o usuário perguntar quais cores estão disponíveis."
            ),
            Tool(
                name="list_all_paints",
                func=list_all_paints,
                description="Lista todas as tintas do catálogo. Use apenas quando solicitado explicitamente."
            )
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
            response_text = self._postprocess_response(response_text)

            # Extrair IDs e ferramentas usadas
            tools_used, paints_mentioned = [], []
            for step in result.get("intermediate_steps", []):
                try:
                    if len(step) >= 2:
                        action, observation = step[0], step[1]
                        tool_name = getattr(action, 'tool', str(action))
                        tools_used.append({"tool": tool_name})
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
            raise

    # -------------------------------------------------------------------
    # Pós-processamento (desativado para respostas diretas)
    # -------------------------------------------------------------------
    def _postprocess_response(self, text: str) -> str:
        # Retorna texto original sem reescrita para manter tom consultivo direto
        return text

    def reset_memory(self):
        logger.info(f"[MEMORY] Resetando memória para user_id={self.user_id}")
        self.memory.clear()
        self.agent = self._create_agent()

    def get_conversation_summary(self) -> str:
        messages = self.memory.chat_memory.messages
        if not messages:
            return "Nenhuma conversa iniciada."
        return f"Conversa com {len(messages)} mensagens."

"""
Serviço de Agente IA com ferramentas, memória e observabilidade.

Este módulo implementa um agente inteligente especialista em tintas Suvinil,
capaz de:
- Interpretar intenções do usuário
- Buscar e recomendar produtos adequados
- Manter contexto da conversa
- Gerar visualizações com IA (opcional)
"""
import json
import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.memory import ConversationBufferWindowMemory

from app.repositories.paint_repository import PaintRepository
from app.models.paint import Environment, FinishType, PaintLine
from app.models.chat_message import ChatMessage
from app.core.config import settings

# Configurar logging estruturado
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SYSTEM PROMPT - Persona do Especialista Suvinil
# ============================================================================

SYSTEM_PROMPT = """Você é um **Assistente Virtual Especialista em Tintas Suvinil**, um profissional experiente
que ajuda clientes a escolherem o produto ideal para suas necessidades de pintura.

## SUA PERSONALIDADE
- Amigável, prestativo e profissional
- Especialista técnico em tintas e pinturas
- Consultor que entende as necessidades do cliente
- Comunicativo e claro nas explicações

## SUAS RESPONSABILIDADES

### 1. INTERPRETAR A INTENÇÃO DO USUÁRIO
Antes de responder, analise o que o usuário realmente precisa:
- **Ambiente**: É interno (quarto, sala, escritório) ou externo (fachada, muro, varanda)?
- **Superfície**: Parede, madeira, metal, etc.?
- **Características desejadas**: Lavável, sem odor, anti-mofo, resistente ao sol/chuva?
- **Cor/Estilo**: Qual cor ou estilo o cliente busca?
- **Linha/Orçamento**: Premium, Standard ou Economy?

### 2. USAR AS FERRAMENTAS CORRETAMENTE
Você tem acesso a ferramentas para buscar informações. USE-AS sempre que precisar:
- `search_paints`: Para buscar tintas por características, ambiente, cor, etc.
- `filter_paints_by_environment`: Para filtrar especificamente por interno/externo
- `get_paint_details`: Para obter detalhes completos de uma tinta
- `list_all_paints`: Para ver todo o catálogo

### 3. FAZER RECOMENDAÇÕES PERSONALIZADAS
Ao recomendar uma tinta:
1. Explique PORQUE ela é adequada para o caso específico
2. Mencione as características principais que atendem às necessidades
3. Sugira alternativas quando apropriado
4. Informe o preço quando disponível

### 4. MANTER O CONTEXTO DA CONVERSA
- Lembre-se do que foi discutido anteriormente
- Faça perguntas de acompanhamento quando necessário
- Ofereça sugestões complementares

## FORMATO DE RESPOSTA

Sempre estruture suas respostas de forma clara:
- Use **negrito** para destacar nomes de produtos
- Organize características em listas quando apropriado
- Seja conciso mas informativo
- Termine oferecendo ajuda adicional

## REGRAS IMPORTANTES

1. **NUNCA invente produtos** - Use apenas as ferramentas para buscar informações
2. **Seja honesto** - Se não encontrar algo, diga e sugira alternativas
3. **Foque na Suvinil** - Você representa a marca Suvinil
4. **Pergunte quando necessário** - Se faltarem informações, pergunte ao cliente
5. **Seja proativo** - Sugira produtos complementares ou cores que combinam

## EXEMPLOS DE INTERAÇÕES

**Usuário**: "Quero pintar meu quarto, mas prefiro algo fácil de limpar e sem cheiro forte."
**Você**: Busque tintas para ambiente interno, com características "lavável" e "sem odor", 
e recomende explicando porque são ideais para quartos.

**Usuário**: "Preciso pintar a fachada da minha casa. Bate muito sol e chove bastante."
**Você**: Busque tintas para ambiente externo com proteção UV e resistência à chuva,
e explique como esses produtos protegem contra intempéries.

**Usuário**: "Quero um cinza parecido com cimento queimado para minha sala."
**Você**: Busque tintas em tons de cinza para ambiente interno e recomende opções
que proporcionem o visual industrial/moderno do cimento queimado.

Agora, ajude o cliente com suas necessidades de pintura!
"""


# ============================================================================
# CLASSE PRINCIPAL DO AGENTE
# ============================================================================

class AgentService:
    """
    Serviço de Agente IA Especialista em Tintas Suvinil.
    
    Implementa um agente com:
    - Ferramentas para busca e análise de tintas
    - Memória de conversa com janela deslizante
    - Logging de decisões para observabilidade
    """
    
    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        
        # Configurar LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Memória com janela de 10 mensagens
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10,
        )
        
        # Carregar histórico do banco se houver user_id
        if user_id:
            self._load_history_from_db()
        
        # Criar agente
        self.agent = self._create_agent()
        
        # Metadados da última execução
        self.last_execution_metadata: Dict[str, Any] = {}
        
        logger.info(f"AgentService inicializado para user_id={user_id}")
    
    def _load_history_from_db(self):
        """Carrega histórico de mensagens do banco de dados"""
        try:
            messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.user_id == self.user_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(20)
                .all()
            )
            
            messages = list(reversed(messages))
            
            for msg in messages:
                if msg.role == "user":
                    self.memory.chat_memory.add_user_message(msg.content)
                elif msg.role == "assistant":
                    self.memory.chat_memory.add_ai_message(msg.content)
            
            logger.info(f"Carregadas {len(messages)} mensagens do histórico")
        except Exception as e:
            logger.warning(f"Erro ao carregar histórico: {e}")
    
    def _save_message_to_db(self, role: str, content: str):
        """Salva mensagem no banco de dados"""
        if not self.user_id:
            return
        
        try:
            message = ChatMessage(
                user_id=self.user_id,
                role=role,
                content=content,
                created_at=datetime.utcnow(),
            )
            self.db.add(message)
            self.db.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
            self.db.rollback()
    
    # ========================================================================
    # FERRAMENTAS DO AGENTE
    # ========================================================================
    
    def _create_tools(self) -> List[Tool]:
        """Cria ferramentas disponíveis para o agente"""
        
        # 1. Busca de tintas
        def search_paints(query: str) -> str:
            """Busca tintas baseado na consulta do usuário"""
            logger.info(f"[TOOL] search_paints: query='{query}'")
            
            # Buscar todas as tintas e filtrar por relevância
            all_paints = PaintRepository.get_all(self.db, limit=100)
            
            if not all_paints:
                return "Nenhuma tinta encontrada no catálogo."
            
            query_lower = query.lower()
            
            # Palavras-chave para matching
            keywords = query_lower.split()
            
            # Pontuar cada tinta
            scored_paints = []
            for paint in all_paints:
                score = 0
                paint_text = f"{paint.name} {paint.color_name or ''} {paint.description or ''} {paint.features or ''} {paint.environment.value} {paint.finish_type.value}".lower()
                
                for keyword in keywords:
                    if keyword in paint_text:
                        score += 1
                    # Palavras especiais
                    if keyword in ["cinza", "grey", "gray", "cimento", "concreto", "urbano"] and "cinza" in paint_text:
                        score += 2
                    if keyword in ["interno", "interior", "quarto", "sala", "escritório"] and paint.environment.value in ["interno", "ambos"]:
                        score += 2
                    if keyword in ["externo", "exterior", "fachada", "muro"] and paint.environment.value in ["externo", "ambos"]:
                        score += 2
                    if keyword in ["lavável", "lavavel", "limpar", "limpeza"] and paint.features and "lavável" in paint.features.lower():
                        score += 2
                    if keyword in ["odor", "cheiro"] and paint.features and "sem odor" in paint.features.lower():
                        score += 2
                
                if score > 0:
                    scored_paints.append((paint, score))
            
            # Ordenar por pontuação
            scored_paints.sort(key=lambda x: x[1], reverse=True)
            
            # Pegar top 5
            top_paints = scored_paints[:5] if scored_paints else [(p, 0) for p in all_paints[:5]]
            
            result = "**Tintas encontradas:**\n\n"
            for paint, score in top_paints:
                features = paint.features.split(",") if paint.features else []
                features_text = ", ".join([f.strip() for f in features[:4]])
                
                result += f"**{paint.name}** (ID: {paint.id})\n"
                result += f"  - Cor: {paint.color_name or 'Variável'}\n"
                result += f"  - Ambiente: {paint.environment.value}\n"
                result += f"  - Acabamento: {paint.finish_type.value}\n"
                result += f"  - Linha: {paint.line.value}\n"
                if features_text:
                    result += f"  - Características: {features_text}\n"
                if paint.price:
                    result += f"  - Preço: R$ {paint.price:.2f}\n"
                if paint.description:
                    desc = paint.description[:100] + "..." if len(paint.description) > 100 else paint.description
                    result += f"  - {desc}\n"
                result += "\n"
            
            return result
        
        # 2. Filtro por ambiente
        def filter_by_environment(environment: str) -> str:
            """Filtra tintas por tipo de ambiente"""
            logger.info(f"[TOOL] filter_by_environment: environment='{environment}'")
            
            env_map = {
                "interno": Environment.INTERIOR,
                "interior": Environment.INTERIOR,
                "externo": Environment.EXTERIOR,
                "exterior": Environment.EXTERIOR,
                "ambos": Environment.BOTH,
            }
            
            env = env_map.get(environment.lower())
            if not env:
                return f"Ambiente '{environment}' não reconhecido. Use: interno, externo ou ambos."
            
            paints = PaintRepository.get_all(self.db, environment=env, limit=10)
            
            if not paints:
                return f"Nenhuma tinta encontrada para ambiente {environment}."
            
            result = f"**Tintas para ambiente {environment}:**\n\n"
            for paint in paints:
                features = paint.features.split(",") if paint.features else []
                features_text = ", ".join([f.strip() for f in features[:3]])
                result += f"• **{paint.name}** - {paint.color_name or 'Várias cores'}\n"
                result += f"  Acabamento: {paint.finish_type.value} | Linha: {paint.line.value}\n"
                if features_text:
                    result += f"  Características: {features_text}\n"
                if paint.price:
                    result += f"  Preço: R$ {paint.price:.2f}\n"
                result += "\n"
            
            return result
        
        # 3. Detalhes de tinta específica
        def get_paint_details(paint_id: str) -> str:
            """Obtém detalhes completos de uma tinta"""
            logger.info(f"[TOOL] get_paint_details: paint_id={paint_id}")
            
            try:
                pid = int(paint_id)
                paint = PaintRepository.get_by_id(self.db, pid)
                if not paint or not paint.is_active:
                    return f"Tinta com ID {paint_id} não encontrada."
                
                features_list = paint.features.split(",") if paint.features else []
                features_text = ", ".join([f.strip() for f in features_list])
                
                result = f"""**{paint.name}**

📋 **Informações Gerais**
- Cor: {paint.color_name or paint.color or "Não especificada"}
- Código: {paint.color or "N/A"}

🎨 **Especificações**
- Superfície: {paint.surface_type or "Múltiplas"}
- Ambiente: {paint.environment.value}
- Acabamento: {paint.finish_type.value}
- Linha: {paint.line.value}

✨ **Características**
{features_text if features_text else "Padrão"}

📝 **Descrição**
{paint.description or "Tinta de qualidade Suvinil."}
"""
                if paint.price:
                    result += f"\n💰 **Preço**: R$ {paint.price:.2f}"
                
                return result
            except Exception as e:
                return f"Erro ao buscar detalhes: {str(e)}"
        
        # 4. Listar todas as tintas
        def list_all_paints(_: str = "") -> str:
            """Lista todas as tintas disponíveis no catálogo"""
            logger.info("[TOOL] list_all_paints")
            
            paints = PaintRepository.get_all(self.db, skip=0, limit=50)
            if not paints:
                return "Nenhuma tinta disponível no catálogo."
            
            result = f"**Catálogo de Tintas Suvinil** ({len(paints)} produtos)\n\n"
            
            # Agrupar por linha
            by_line = {}
            for paint in paints:
                line = paint.line.value
                if line not in by_line:
                    by_line[line] = []
                by_line[line].append(paint)
            
            for line, line_paints in by_line.items():
                result += f"**Linha {line}:**\n"
                for paint in line_paints[:10]:
                    result += f"  • {paint.name} - {paint.color_name or 'Várias'} (ID: {paint.id})\n"
                if len(line_paints) > 10:
                    result += f"  ... e mais {len(line_paints) - 10} produtos\n"
                result += "\n"
            
            return result
        
        # Montar lista de ferramentas
        tools = [
            Tool(
                name="search_paints",
                func=search_paints,
                description="""Busca tintas no catálogo. Use para encontrar tintas baseado em:
- Características (lavável, sem odor, anti-mofo)
- Cores (cinza, branco, azul)
- Ambiente (interno, externo)
- Tipo de superfície (parede, madeira)
Exemplo: 'cinza para sala lavável'"""
            ),
            Tool(
                name="filter_paints_by_environment",
                func=filter_by_environment,
                description="""Filtra tintas por ambiente: 'interno', 'externo' ou 'ambos'.
Use quando o usuário especificar claramente o tipo de ambiente."""
            ),
            Tool(
                name="get_paint_details",
                func=get_paint_details,
                description="""Obtém detalhes de uma tinta específica usando seu ID numérico.
Use quando precisar de informações completas sobre uma tinta."""
            ),
            Tool(
                name="list_all_paints",
                func=list_all_paints,
                description="""Lista todas as tintas do catálogo.
Use quando o usuário pedir para ver todas as opções disponíveis."""
            ),
        ]
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Cria agente com ferramentas e prompt otimizado"""
        tools = self._create_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
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
            max_iterations=5,
            return_intermediate_steps=True,
        )
        
        return agent_executor
    
    def chat(self, message: str) -> Dict[str, Any]:
        """
        Processa mensagem do usuário e retorna resposta do agente.
        """
        logger.info(f"[CHAT] Recebida mensagem: '{message[:50]}...'")
        
        try:
            # Obter histórico da memória
            chat_history = self.memory.chat_memory.messages
            
            # Preparar contexto
            input_dict = {
                "input": message,
                "chat_history": chat_history if chat_history else [],
            }
            
            # Executar agente
            start_time = datetime.utcnow()
            result = self.agent.invoke(input_dict)
            end_time = datetime.utcnow()
            
            # Extrair resposta
            response_text = result.get("output", "Desculpe, não consegui processar sua mensagem.")
            
            # Extrair ferramentas usadas
            tools_used = []
            paints_mentioned = []
            intermediate_steps = result.get("intermediate_steps", [])
            
            for step in intermediate_steps:
                try:
                    if len(step) >= 2:
                        action = step[0]
                        observation = step[1]
                        
                        # Extrair nome da ferramenta e input
                        tool_name = getattr(action, 'tool', str(action))
                        tool_input = getattr(action, 'tool_input', '')
                        
                        tools_used.append({
                            "tool": tool_name,
                            "input": str(tool_input),
                        })
                        
                        # Extrair IDs de tintas
                        if "ID:" in str(observation):
                            ids = re.findall(r'ID:\s*(\d+)', str(observation))
                            paints_mentioned.extend([int(i) for i in ids])
                except Exception as e:
                    logger.warning(f"Erro ao processar step: {e}")
            
            # Salvar na memória
            self.memory.chat_memory.add_user_message(message)
            self.memory.chat_memory.add_ai_message(response_text)
            
            # Salvar no banco de dados
            self._save_message_to_db("user", message)
            self._save_message_to_db("assistant", response_text)
            
            # Preparar metadados
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            self.last_execution_metadata = {
                "tools_used": tools_used,
                "paints_mentioned": list(set(paints_mentioned)),
                "execution_time_ms": execution_time,
                "intermediate_steps_count": len(intermediate_steps),
            }
            
            logger.info(f"[CHAT] Resposta gerada em {execution_time:.0f}ms. Ferramentas: {[t['tool'] for t in tools_used]}")
            
            return {
                "response": response_text,
                "tools_used": tools_used,
                "paints_mentioned": list(set(paints_mentioned)),
                "metadata": self.last_execution_metadata,
            }
            
        except Exception as e:
            logger.error(f"[CHAT] Erro ao processar mensagem: {e}", exc_info=True)
            return {
                "response": f"Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                "tools_used": [],
                "paints_mentioned": [],
                "metadata": {"error": str(e)},
            }
    
    def reset_memory(self):
        """Reseta memória da conversa"""
        logger.info(f"[MEMORY] Resetando memória para user_id={self.user_id}")
        self.memory.clear()
        self.agent = self._create_agent()
    
    def get_conversation_summary(self) -> str:
        """Retorna um resumo da conversa atual"""
        messages = self.memory.chat_memory.messages
        if not messages:
            return "Nenhuma conversa iniciada."
        return f"Conversa com {len(messages)} mensagens."

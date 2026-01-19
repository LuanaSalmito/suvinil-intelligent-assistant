"""
Agente Orquestrador Multi-Especialistas

Este agente coordena múltiplos especialistas, decide qual consultar
e combina suas recomendações para fornecer a melhor resposta ao usuário.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.ai.specialists import (
    get_all_specialists,
    InteriorEnvironmentSpecialist,
    ExteriorEnvironmentSpecialist,
    ColorAndFinishSpecialist,
    DurabilitySpecialist
)
from app.ai.image_generator import ImageGenerator
from app.models.chat_message import ChatMessage
from app.core.config import settings

logger = logging.getLogger(__name__)


ORCHESTRATOR_SYSTEM_PROMPT = """Você é um Assistente Inteligente Suvinil, especialista em recomendações de tintas.

Você coordena uma equipe de especialistas:
- Especialista em Ambientes Internos (quartos, salas, banheiros)
- Especialista em Ambientes Externos (fachadas, muros, varandas)  
- Especialista em Cores e Acabamentos (psicologia das cores, harmonização)
- Especialista em Durabilidade (madeira, metal, resistência)

SEU PAPEL:
1. Analisar a mensagem do usuário
2. Identificar qual(is) especialista(s) consultar
3. Interpretar as recomendações dos especialistas
4. Fornecer uma resposta natural, clara e objetiva

ESTILO DE RESPOSTA:
- Tom consultivo e profissional
- Respostas diretas e concisas (3-4 frases)
- Sugira APENAS 1 produto por vez
- Explique brevemente POR QUE é a melhor escolha
- Termine com uma pergunta de follow-up curta
- NÃO use emojis ou linguagem excessivamente casual

REGRAS IMPORTANTES:
- SEMPRE mencione qual especialista foi consultado
- Se o usuário pedir visualização, informe que pode gerar
- Mantenha o contexto da conversa anterior
- Se não tiver certeza, pergunte ao usuário

EXEMPLO DE RESPOSTA CORRETA:
"Consultei nosso especialista em ambientes internos. Para quartos com crianças, 
recomendo a Suvinil Fosco Completo Azul, pois é lavável, sem odor e resistente. 
R$ 89,90. Quer ver como ficaria no ambiente?"
"""


class OrchestratorAgent:
    """
    Agente Orquestrador que coordena especialistas e gera respostas contextuais
    """
    
    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        
        # LLM para geração de respostas naturais
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
        
        # Carregar histórico do banco
        if user_id:
            self._load_history_from_db()
        
        # Especialistas disponíveis
        self.specialists = get_all_specialists(db)
        
        # Gerador de imagens (opcional)
        try:
            self.image_generator = ImageGenerator()
        except Exception as e:
            logger.warning(f"Image generator não disponível: {e}")
            self.image_generator = None
        
        # Metadados da última execução
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
    
    def _extract_context(self, message: str) -> Dict[str, Any]:
        """Extrai contexto da mensagem e do histórico"""
        message_lower = message.lower()
        
        # Extrair cor
        color_map = {
            "azul": ["azul", "blue"],
            "vermelho": ["vermelho", "red"],
            "verde": ["verde", "green"],
            "amarelo": ["amarelo", "yellow"],
            "branco": ["branco", "white"],
            "cinza": ["cinza", "gray", "grey"],
            "rosa": ["rosa", "pink"],
            "roxo": ["roxo", "violeta", "lilás"],
            "laranja": ["laranja", "orange"],
            "bege": ["bege", "nude"],
        }
        
        color = None
        for color_key, variations in color_map.items():
            if any(var in message_lower for var in variations):
                color = color_key
                break
        
        # Extrair acabamento
        finish_type = None
        if "fosco" in message_lower:
            finish_type = "fosco"
        elif "brilhante" in message_lower:
            finish_type = "brilhante"
        elif "semi-brilhante" in message_lower or "semi brilhante" in message_lower:
            finish_type = "semi-brilhante"
        elif "acetinado" in message_lower:
            finish_type = "acetinado"
        
        # Extrair ambiente
        environment = None
        room_type = None
        if any(word in message_lower for word in ["quarto", "dormitório"]):
            environment = "interno"
            room_type = "quarto"
        elif any(word in message_lower for word in ["sala", "living"]):
            environment = "interno"
            room_type = "sala"
        elif any(word in message_lower for word in ["escritório", "escritorio", "home office"]):
            environment = "interno"
            room_type = "escritório"
        elif any(word in message_lower for word in ["banheiro", "lavabo"]):
            environment = "interno"
            room_type = "banheiro"
        elif any(word in message_lower for word in ["cozinha"]):
            environment = "interno"
            room_type = "cozinha"
        elif any(word in message_lower for word in ["interno", "interior"]):
            environment = "interno"
        elif any(word in message_lower for word in ["fachada", "exterior"]):
            environment = "externo"
            room_type = "fachada"
        elif any(word in message_lower for word in ["externo", "muro", "varanda"]):
            environment = "externo"
        
        # Detectar pedido de visualização
        wants_visualization = any(word in message_lower for word in [
            "mostra", "mostrar", "ver", "visualizar", "imagem", "como ficaria",
            "pode mostrar", "gostaria de ver", "quero ver", "me mostra"
        ])
        
        # Se não encontrou contexto na mensagem atual, buscar no histórico
        if not color or not environment or not finish_type:
            chat_history = self.memory.chat_memory.messages
            recent_messages = chat_history[-6:] if len(chat_history) > 0 else []
            
            for msg in reversed(recent_messages):
                if not hasattr(msg, 'content'):
                    continue
                msg_lower = msg.content.lower()
                
                # Buscar cor no histórico
                if not color:
                    for color_key, variations in color_map.items():
                        if any(var in msg_lower for var in variations):
                            color = color_key
                            break
                
                # Buscar ambiente no histórico
                if not environment:
                    if any(word in msg_lower for word in ["quarto", "dormitório"]):
                        environment = "interno"
                        room_type = "quarto"
                    elif any(word in msg_lower for word in ["sala", "living"]):
                        environment = "interno"
                        room_type = "sala"
                    elif any(word in msg_lower for word in ["escritório", "escritorio", "home office"]):
                        environment = "interno"
                        room_type = "escritório"
                    elif any(word in msg_lower for word in ["banheiro", "lavabo"]):
                        environment = "interno"
                        room_type = "banheiro"
                    elif any(word in msg_lower for word in ["interno", "interior"]):
                        environment = "interno"
                    elif any(word in msg_lower for word in ["externo", "fachada", "muro", "varanda"]):
                        environment = "externo"
                
                # Buscar acabamento no histórico
                if not finish_type:
                    if "semi-brilhante" in msg_lower or "semi brilhante" in msg_lower:
                        finish_type = "semi-brilhante"
                    elif "fosco" in msg_lower:
                        finish_type = "fosco"
                    elif "brilhante" in msg_lower:
                        finish_type = "brilhante"
                    elif "acetinado" in msg_lower:
                        finish_type = "acetinado"
                
                # Se já encontrou tudo, pode parar
                if color and environment and finish_type:
                    break
        
        return {
            "color": color,
            "finish_type": finish_type,
            "environment": environment,
            "room_type": room_type,
            "wants_visualization": wants_visualization,
            "original_message": message
        }
    
    def _select_specialists(self, message: str, context: Dict[str, Any]) -> List[Any]:
        """Seleciona quais especialistas consultar"""
        selected = []
        
        for specialist in self.specialists:
            if specialist.can_handle(message, context):
                selected.append(specialist)
                logger.info(f"Selecionado: {specialist.name}")
        
        # Se nenhum especialista foi selecionado, usar o de cores como fallback
        if not selected:
            selected = [s for s in self.specialists if isinstance(s, ColorAndFinishSpecialist)]
        
        return selected
    
    def _consult_specialists(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Consulta os especialistas selecionados"""
        specialists = self._select_specialists(message, context)
        
        results = []
        for specialist in specialists:
            try:
                result = specialist.consult(message, context)
                results.append(result)
                logger.info(
                    f"[{specialist.name}] Retornou {len(result.get('recommendations', []))} recomendações "
                    f"(confiança: {result.get('confidence', 0):.2f})"
                )
            except Exception as e:
                logger.error(f"Erro ao consultar {specialist.name}: {e}")
        
        return results
    
    def _generate_response(
        self,
        message: str,
        context: Dict[str, Any],
        specialist_results: List[Dict[str, Any]]
    ) -> str:
        """Gera resposta natural baseada nas consultas dos especialistas"""
        
        if not specialist_results:
            return "Desculpe, não consegui encontrar recomendações adequadas. Pode me dar mais detalhes sobre o que precisa?"
        
        # Preparar contexto para o LLM
        specialists_info = []
        all_recommendations = []
        
        for result in specialist_results:
            specialists_info.append({
                "specialist": result["specialist"],
                "reasoning": result["reasoning"],
                "confidence": result.get("confidence", 0)
            })
            all_recommendations.extend(result.get("recommendations", []))
        
        # Se não tem recomendações mas tem cores disponíveis
        if not all_recommendations:
            for result in specialist_results:
                if "available_colors" in result:
                    colors_list = ", ".join([
                        f"{c['color_display']} ({c['count']} opções)"
                        for c in result["available_colors"][:8]
                    ])
                    return f"Temos diversas cores disponíveis no catálogo: {colors_list}. Qual cor você prefere?"
        
        # Pegar a melhor recomendação
        best_recommendation = all_recommendations[0] if all_recommendations else None
        
        if not best_recommendation:
            return "Não encontrei tintas que correspondam exatamente ao que você busca. Pode me dar mais detalhes?"
        
        # Preparar prompt para o LLM
        system_message = ORCHESTRATOR_SYSTEM_PROMPT
        
        specialist_names = [s["specialist"] for s in specialists_info]
        reasoning_text = " | ".join([s["reasoning"] for s in specialists_info])
        
        # Informações da tinta recomendada
        paint_info = f"""
CONSULTA REALIZADA:
- Especialistas consultados: {', '.join(specialist_names)}
- Raciocínio: {reasoning_text}

MELHOR RECOMENDAÇÃO:
- Nome: {best_recommendation['name']}
- Cor: {best_recommendation.get('color', 'Várias cores')}
- Acabamento: {best_recommendation['finish']}
- Linha: {best_recommendation['line']}
- Preço: R$ {best_recommendation.get('price', 0):.2f}
- Características: {best_recommendation.get('features', 'Alta qualidade')}
"""
        
        if 'match_reasons' in best_recommendation:
            paint_info += f"- Razões da escolha: {', '.join(best_recommendation['match_reasons'])}\n"
        
        if 'color_psychology' in best_recommendation and best_recommendation.get('color_psychology'):
            paint_info += f"- Sobre a cor: {best_recommendation['color_psychology']}\n"
        
        user_prompt = f"""
Mensagem do usuário: "{message}"

{paint_info}

Gere uma resposta natural e consultiva seguindo o estilo definido.
Mencione qual especialista consultou e explique brevemente por que esta é a melhor escolha.
"""
        
        # Gerar resposta com LLM
        try:
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Se o usuário quer visualização, adicionar menção
            if context.get("wants_visualization") and self.image_generator:
                response_text += "\n\nPosso gerar uma imagem mostrando como ficaria essa tinta aplicada. Quer ver?"
            
            return response_text
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com LLM: {e}")
            # Fallback: resposta simples baseada nos dados
            features_text = ", ".join(best_recommendation.get('match_reasons', [])[:2])
            return (
                f"Recomendo a {best_recommendation['name']} - {best_recommendation.get('color', 'cor disponível')}. "
                f"{features_text if features_text else 'Qualidade Suvinil'}, "
                f"acabamento {best_recommendation['finish']}. "
                f"R$ {best_recommendation.get('price', 0):.2f}. "
                f"É o que você procura?"
            )
    
    async def _generate_visualization(
        self,
        paint_info: Dict[str, Any],
        environment_description: str
    ) -> Optional[str]:
        """Gera visualização da tinta aplicada"""
        if not self.image_generator:
            return None
        
        try:
            image_url = await self.image_generator.generate_paint_visualization(
                color=paint_info.get("color", "branco"),
                environment=environment_description,
                finish=paint_info.get("finish", "fosco")
            )
            return image_url
        except Exception as e:
            logger.error(f"Erro ao gerar visualização: {e}")
            return None
    
    def chat(self, message: str) -> Dict[str, Any]:
        """
        Processa mensagem do usuário e retorna resposta orquestrada
        """
        logger.info(f"[ORCHESTRATOR] Mensagem recebida: '{message[:50]}...'")
        
        start_time = datetime.utcnow()
        
        try:
            # Extrair contexto
            context = self._extract_context(message)
            logger.info(f"[ORCHESTRATOR] Contexto extraído: {context}")
            
            # Consultar especialistas
            specialist_results = self._consult_specialists(message, context)
            
            # Gerar resposta
            response_text = self._generate_response(message, context, specialist_results)
            
            # Coletar IDs de tintas mencionadas
            paints_mentioned = []
            for result in specialist_results:
                for rec in result.get("recommendations", []):
                    if "paint_id" in rec:
                        paints_mentioned.append(rec["paint_id"])
            
            # Salvar na memória e banco
            self.memory.chat_memory.add_user_message(message)
            self.memory.chat_memory.add_ai_message(response_text)
            self._save_message_to_db("user", message)
            self._save_message_to_db("assistant", response_text)
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            # Preparar metadados
            specialists_used = [
                {"specialist": r["specialist"], "confidence": r.get("confidence", 0)}
                for r in specialist_results
            ]
            
            self.last_execution_metadata = {
                "specialists_consulted": specialists_used,
                "total_recommendations": sum(len(r.get("recommendations", [])) for r in specialist_results),
                "paints_mentioned": list(set(paints_mentioned)),
                "execution_time_ms": execution_time,
                "context_extracted": context
            }
            
            return {
                "response": response_text,
                "specialists_consulted": specialists_used,
                "paints_mentioned": list(set(paints_mentioned)),
                "metadata": self.last_execution_metadata,
                "reasoning_chain": [
                    {
                        "specialist": r["specialist"],
                        "reasoning": r["reasoning"],
                        "recommendations_count": len(r.get("recommendations", []))
                    }
                    for r in specialist_results
                ]
            }
            
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Erro: {e}", exc_info=True)
            raise
    
    def reset_memory(self):
        """Reseta memória de conversa"""
        logger.info(f"[ORCHESTRATOR] Resetando memória para user_id={self.user_id}")
        self.memory.clear()
    
    def get_conversation_summary(self) -> str:
        """Retorna resumo da conversa"""
        messages = self.memory.chat_memory.messages
        if not messages:
            return "Nenhuma conversa iniciada."
        return f"Conversa com {len(messages)} mensagens. Especialistas disponíveis: {len(self.specialists)}."

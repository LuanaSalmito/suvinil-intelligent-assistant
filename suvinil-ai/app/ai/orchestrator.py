import logging
import time
from typing import List, Dict, Any, Optional
import re
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from sqlalchemy.orm import Session

from app.ai.rag_service import RAGService
from app.ai.specialists import get_all_specialists, SpecialistRecommendation
from app.ai.image_generator import ImageGenerator
from app.repositories.paint_repository import PaintRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

class PaintContext(BaseModel):
    environment: Optional[str] = Field(None, description="interno ou externo")
    surface_type: Optional[str] = Field(None, description="parede, madeira, metal, etc")
    color: Optional[str] = Field(None, description="cor mencionada")
    finish_type: Optional[str] = Field(None, description="fosco, acetinado ou brilhante")

class OrchestratorAgent:
    """
    Orquestrador Avançado: Atua como Consultor Técnico de Tintas utilizando 
    raciocínio lógico e empatia com o projeto do usuário.
    """
    
    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.rag = RAGService(db)
        # IMPORTANTE: ChatOpenAI não lê automaticamente settings.OPENAI_API_KEY.
        # Se não passarmos explicitamente, o orquestrador cai no fallback.
        self.llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0,
            openai_api_key=(settings.OPENAI_API_KEY or "").strip().strip('"').strip("'"),
        )
        self.parser = PydanticOutputParser(pydantic_object=PaintContext)
        self.image_generator = ImageGenerator()
        self.conversation_memory: List[Dict] = []
        # Memória “de slots” (persistente) para follow-ups tipo: "e fosco ou acetinado?"
        self.slot_memory: PaintContext = PaintContext()
        
        self.style_guide = """
        VOCÊ É UM CONSULTOR TÉCNICO ESPECIALISTA EM ACABAMENTOS E CORES.
        
        REGRAS IMPORTANTES:
        - Não mostre seu raciocínio passo a passo.
        - Não repita cabeçalhos, JSON, "DADOS DO PRODUTO" ou textos de sistema.
        - Escreva como um humano: direto, consultivo, sem linguagem de debug.
        
        DIRETRIZES DE ESTILO:
        - Respostas naturais e humanas, sem parecer um robô de busca.
        - Máximo de 4 frases curtas e impactantes.
        - NUNCA use emojis.
        - Sugira apenas 1 produto (o melhor para o caso).
        - Termine com uma pergunta consultiva que demonstre interesse no projeto.
        """

    def reset_memory(self):
        self.conversation_memory = []
        self.slot_memory = PaintContext()

    def _is_price_query(self, text: str) -> bool:
        """
        Consulta de preço deve ser respondida direto do catálogo (sem LLM),
        para evitar custos/latência e reduzir risco de alucinação de valores.
        """
        m = (text or "").strip().lower()
        if not m:
            return False
        keywords = ["preço", "preco", "valor", "custo", "quanto", "caro", "barato"]
        if any(k in m for k in keywords):
            return True
        return bool(re.search(r"\bquanto\s+custa\b|\bqual\s+o\s+pre[cç]o\b", m))

    def _price_catalog_response(self) -> Dict[str, Any]:
        paints = PaintRepository.get_all(self.db, skip=0, limit=100)
        lines: List[str] = []
        paints_mentioned: List[int] = []
        for p in paints:
            color_label = p.cor or "Cor variável"
            lines.append(f"• **{p.nome} - {color_label}** ({p.linha.value})")
            paints_mentioned.append(p.id)
        if not lines:
            response = "No momento, não encontrei tintas cadastradas no catálogo."
        else:
            response = "Aqui estão as tintas do catálogo:\n\n" + "\n".join(lines)
        return {
            "response": response,
            "context": {},
            "paints_mentioned": paints_mentioned,
            "specialists_consulted": [],
            "reasoning_chain": [],
        }

    async def chat(self, user_input: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        start_time = time.time()
        tools_used: List[Dict[str, str]] = []

        # Preço: responder sem LLM (evita até extração de contexto)
        if self._is_price_query(user_input):
            result = self._price_catalog_response()
            result["metadata"] = {"execution_time_ms": (time.time() - start_time) * 1000}
            result["tools_used"] = [{"tool": "db_list_catalog", "input": "price_query"}]
            return result

        self.conversation_memory.append({"role": "user", "content": user_input})
        
        # 1. Extração de Contexto (Slots)
        context = self._extract_context(user_input, self.conversation_memory, self.slot_memory)
        # Merge de slots: mantém memória do que já foi definido antes
        merged = PaintContext(
            environment=context.environment or self.slot_memory.environment,
            surface_type=context.surface_type or self.slot_memory.surface_type,
            color=context.color or self.slot_memory.color,
            finish_type=context.finish_type or self.slot_memory.finish_type,
        )
        self.slot_memory = merged
        context_dict = merged.dict()
        # Contexto no formato esperado pelos especialistas (retrocompatibilidade)
        specialist_context = {
            "ambiente": merged.environment,
            "tipo_parede": merged.surface_type,
            "cor": merged.color,
            "acabamento": merged.finish_type,
        }
        
        # 2. Verificação de Slots Críticos (Fluxo de Diálogo)
        missing = self._get_missing_slots(merged)
        # Se não tem nem ambiente nem cor, perguntar o mínimo (evita loop)
        if not merged.environment and not merged.color:
            response = self._ask_for_missing(missing)
            self.conversation_memory.append({"role": "assistant", "content": response})
            return {
                "response": response,
                "context": context_dict,
                "paints_mentioned": [],
                "tools_used": tools_used,
                "metadata": {"execution_time_ms": (time.time() - start_time) * 1000}
            }

        # 3. Consulta aos Especialistas (Inteligência de Negócio)
        specialists = get_all_specialists(self.db)
        specialist_recommendations: List[SpecialistRecommendation] = []
        for specialist in specialists:
            # Segurança: alguns especialistas podem não implementar can_help (ou mudar no futuro)
            can_help_fn = getattr(specialist, "can_help", None)
            can_help = True if not callable(can_help_fn) else bool(can_help_fn(specialist_context))
            if not can_help:
                continue
            rec = specialist.analyze(specialist_context)
            if rec:
                specialist_recommendations.append(rec)
        tools_used.append({"tool": "db_specialists_scan", "input": "PaintRepository.get_all(limit=150)"})
        
        # 4. Síntese do Produto (Melhor Escolha)
        all_paints = []
        for rec in specialist_recommendations:
            all_paints.extend(rec.recommended_paints)
        
        seen_ids = set()
        unique_paints = [p for p in all_paints if not (p.id in seen_ids or seen_ids.add(p.id))]
        best_paint = unique_paints[0] if unique_paints else None

        # Fallback de produto: se especialistas não retornarem tinta, usar RAG para apontar um item do catálogo.
        if best_paint is None:
            try:
                filters = {}
                if merged.environment:
                    filters["ambiente"] = merged.environment
                if merged.color:
                    filters["cor"] = merged.color
                if merged.surface_type:
                    filters["tipo_parede"] = merged.surface_type

                rag_hits = self.rag.search_paints(
                    query=f"Tinta para {merged.environment or ''} {merged.surface_type or ''} cor {merged.color or ''}",
                    k=1,
                    filters=filters or None,
                )
                if rag_hits:
                    tools_used.append({"tool": "rag_search_paints", "input": f"query={user_input} filters={filters or None}"})
                    paint_id = rag_hits[0].get("paint_id")
                    if paint_id:
                        best_paint = PaintRepository.get_by_id(self.db, int(paint_id))
            except Exception as e:
                logger.warning(f"Falha ao usar RAG como fallback de produto: {e}")

        # 5. Prompt de Síntese Final (O Coração da Humanização)
        specialist_insights = "\n".join([f"- {r.specialist_name}: {r.reasoning}" for r in specialist_recommendations])
        
        paint_info = self._format_paint_info(best_paint)

        # Prompt com Engenharia de Contexto
        prompt = ChatPromptTemplate.from_template("""
            {style_guide}
            
            ---
            DADOS DO PRODUTO SELECIONADO:
            {paint_info}
            
            PARECER DOS ESPECIALISTAS TÉCNICOS:
            {specialist_insights}
            
            CONTEXTO ATUAL:
            Ambiente: {env} | Superfície: {surf} | Cor Focada: {color}
            ---
            
            MENSAGEM DO USUÁRIO: "{user_input}"
            
            TAREFA: Como um consultor, gere uma resposta que conecte o produto à necessidade do usuário. 
            Se ele escolheu uma cor, valide a escolha. Não liste dados, narre a solução.
            Responda APENAS com o texto final ao usuário (sem cabeçalhos, sem JSON, sem repetir seções acima).
            
            RESPOSTA DO CONSULTOR:
        """)
        
        chain = prompt | self.llm
        final_res = await chain.ainvoke({
            "style_guide": self.style_guide,
            "paint_info": paint_info,
            "specialist_insights": specialist_insights or "Análise geral de catálogo.",
            "env": merged.environment or "interno/externo",
            "surf": merged.surface_type or "parede",
            "color": merged.color or "sua preferência",
            "user_input": user_input
        })
        
        response_text = getattr(final_res, "content", "")
        # Alguns modelos podem retornar lista/estruturas; normalizar para string.
        if isinstance(response_text, list):
            response_text = " ".join([str(x) for x in response_text]).strip()
        if not isinstance(response_text, str):
            response_text = str(response_text)
        self.conversation_memory.append({"role": "assistant", "content": response_text})

        # 6. Lógica de Imagem e Retorno
        image_url = await self._handle_image_generation(user_input, merged, best_paint)
        if image_url:
            tools_used.append({"tool": "image_generate", "input": f"color={merged.color} env={merged.environment} finish={merged.finish_type or (best_paint.acabamento.value if best_paint else '')}"})
        
        result = {
            "response": response_text,
            "context": context_dict,
            "paints_mentioned": [best_paint.id] if best_paint else [],
            "tools_used": tools_used,
            # Formato compatível com app/api/v1/ai_chat.py (SpecialistConsulted)
            "specialists_consulted": [{"specialist": r.specialist_name, "confidence": r.confidence} for r in specialist_recommendations],
            # Formato compatível com ReasoningStep (ai_chat.py)
            "reasoning_chain": [r.to_dict() for r in specialist_recommendations],
            "metadata": {"execution_time_ms": (time.time() - start_time) * 1000}
        }
        if image_url: result["image_url"] = image_url
        
        return result

    def _format_paint_info(self, paint) -> str:
        if not paint: return "Nenhum produto específico no catálogo."
        return f"""
        Produto: {paint.nome}
        Cor: {paint.cor}
        Acabamento: {paint.acabamento.value}
        Linha: {paint.linha.value}
        Características: {paint.features}
        """

    async def _handle_image_generation(self, user_input, context: PaintContext, best_paint) -> Optional[str]:
        triggers = ["mostrar", "mostra", "visualizar", "ver", "imagem", "foto", "como fica"]
        if any(word in user_input.lower() for word in triggers) and context.color and best_paint:
            try:
                env = "sala" if context.environment == "interno" else "fachada"
                return await self.image_generator.generate_paint_visualization(
                    color=context.color,
                    environment=env,
                    finish=context.finish_type or best_paint.acabamento.value
                )
            except Exception as e:
                logger.error(f"Erro imagem: {e}")
        return None

    def _extract_context(self, user_input: str, history: List[Dict], current_slots: PaintContext) -> PaintContext:
        """
        Extrai slots usando o turno atual + histórico recente + slots já conhecidos.
        Isso dá memória básica para follow-ups curtos (ex.: "e fosco ou acetinado?").
        """
        # Reduzir ruído: só últimos turnos (evita prompt enorme)
        recent = history[-8:] if history else []
        history_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in recent if m.get("content")])

        prompt = ChatPromptTemplate.from_template(
            "Você é um extrator de informações. Retorne APENAS um JSON válido, sem texto extra.\n"
            "Objetivo: preencher os slots de uma conversa sobre pintura.\n"
            "- Se um slot não estiver presente nem puder ser inferido com segurança, use null.\n"
            "- Use o histórico e os slots atuais para resolver follow-ups.\n\n"
            "SLOTS_ATUAIS (podem estar null): {slots_atuais}\n"
            "HISTORICO_RECENTE:\n{history}\n\n"
            "MENSAGEM_ATUAL: {input}\n"
            "{format_instructions}"
        )
        chain = prompt | self.llm | self.parser
        try:
            return chain.invoke({
                "slots_atuais": current_slots.json(),
                "history": history_text,
                "input": user_input,
                "format_instructions": self.parser.get_format_instructions()
            })
        except Exception as e:
            logger.warning(f"Falha ao extrair contexto: {e}")
            return PaintContext()

    def _get_missing_slots(self, context: PaintContext) -> List[str]:
        missing = []
        if not context.environment: missing.append("ambiente (interno/externo)")
        if not context.surface_type: missing.append("tipo de superfície")
        return missing

    def _ask_for_missing(self, missing: List[str]) -> str:
        questions = {
            "ambiente (interno/externo)": "Para te indicar a melhor tecnologia, esse ambiente é interno ou externo?",
            "tipo de superfície": "Em qual superfície faremos a aplicação (parede, madeira ou metal)?"
        }
        return questions.get(missing[0], "Poderia me dar mais detalhes sobre o que você deseja transformar?")
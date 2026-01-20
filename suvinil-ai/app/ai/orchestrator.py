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
<<<<<<< HEAD
=======
from app.ai.prompts import prompt_manager
>>>>>>> feature/front-configs
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
 
        self.llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0,
            openai_api_key=(settings.OPENAI_API_KEY or "").strip().strip('"').strip("'"),
        )
        self.parser = PydanticOutputParser(pydantic_object=PaintContext)
        self.image_generator = ImageGenerator()
        self.conversation_memory: List[Dict] = []
        self.slot_memory: PaintContext = PaintContext()
        
<<<<<<< HEAD
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
        - NÃO termine com perguntas. Só faça perguntas quando for estritamente necessário para destravar a recomendação.
        """
=======
        self.prompts = prompt_manager.get_orchestrator_prompts()
        self.style_guide = self.prompts.get('style_guide', '')
>>>>>>> feature/front-configs

    def reset_memory(self):
        self.conversation_memory = []
        self.slot_memory = PaintContext()

    def _is_follow_up(self, text: str) -> bool:
        """
        Heurística: follow-up tende a ser curto e referir-se ao que já foi dito
        (ex.: "e fosco ou acetinado?", "pode ser", "e na cor azul?").
        Para mensagens de "novo pedido" (ex.: "quero pintar meu escritório de cinza"),
        NÃO devemos herdar slots antigos (evita 'vazar' madeira/externo de outra conversa).
        """
        t = (text or "").strip().lower()
        if not t:
            return True
        # Mensagens muito curtas geralmente são continuação
        if len(t) <= 28:
            return True
        followup_starters = ("e ", "e se", "e na", "e no", "e para", "e quanto", "ok", "sim", "isso", "pode", "pode ser")
        if t.startswith(followup_starters):
            return True
        # Perguntas sobre acabamento/cor sem "pintar X" costumam ser refinamento
        if any(k in t for k in ["fosco", "acetinado", "brilhante"]) and "pintar" not in t:
            return True
        return False

    def _infer_room_context(self, text: str) -> PaintContext:
        """
        Inferências leves para evitar travar em perguntas óbvias.
        Ex.: "escritório/quarto/sala" -> ambiente interno e superfície parede (se não houver outra).
        """
        t = (text or "").lower()
        if not t:
            return PaintContext()
        # Se falar em madeira/metal explicitamente, não inferir parede.
        if any(k in t for k in ["madeira", "mdf", "compensado", "laminado", "metal", "ferro", "aço", "aco", "alum", "inox"]):
            return PaintContext()
        # Ambientes externos típicos (o usuário nem sempre diz "externo")
        if any(k in t for k in ["fachada", "muro", "área externa", "area externa", "exterior", "varanda", "quintal", "jardim"]):
            return PaintContext(environment="externo", surface_type="parede")
        if any(k in t for k in ["escritório", "escritorio", "quarto", "sala", "cozinha", "banheiro", "lavabo"]):
            return PaintContext(environment="interno", surface_type="parede")
        return PaintContext()

    def _normalize_surface_type(self, surface_type: Optional[str], user_input: str = "") -> Optional[str]:
        """
        Normaliza termos que o usuário usa como "local" (ex.: 'fachada', 'muro')
        para uma superfície que existe no nosso catálogo (ex.: 'parede').
        Motivo: `PaintRepository.recommend_candidates` filtra por `tipo_parede`,
        então 'fachada' tende a zerar candidatos mesmo havendo tintas externas.
        """
        raw = (surface_type or "").strip().lower()
        t = ((user_input or "") + " " + (surface_type or "")).lower()
        if not raw and not t:
            return surface_type

        # "fachada/muro" são locais; no catálogo normalmente isso é "parede/alvenaria"
        if any(k in t for k in ["fachada", "muro", "parede externa", "parede de fora", "exterior da casa"]):
            return "parede"

        # Normalizações leves
        if "parede" in t:
            return "parede"

        return surface_type

    def _extract_feature_intents(self, text: str) -> List[str]:
        """
        Extrai intenções técnicas a partir do texto do usuário para priorizar
        tintas cujo campo `features` contenha os requisitos (lavável/anti-mofo/etc).
        Retorna uma lista de "intents" normalizados.
        """
        t = (text or "").strip().lower()
        if not t:
            return []

        intents: List[str] = []
        if any(k in t for k in ["lavável", "lavavel", "limpar", "limpeza"]):
            intents.append("lavavel")
        if any(k in t for k in ["mofo", "antimofo", "anti-mofo", "umidade", "umidade"]):
            intents.append("antimofo")
        if any(k in t for k in ["sem cheiro", "sem odor", "baixo odor", "pouco cheiro"]):
            intents.append("sem_odor")
        if any(k in t for k in ["alta cobertura", "cobre bem", "boa cobertura", "rende"]):
            intents.append("cobertura")
        if any(k in t for k in ["resistente", "durável", "duravel", "não descasca", "nao descasca"]):
            intents.append("resistencia")
        if any(k in t for k in ["sol", "uv", "chuva", "tempo", "intempérie", "intemperie"]):
            intents.append("clima")
        return intents

    def _score_paint_by_intents(self, paint: Any, intents: List[str]) -> int:
        if not paint or not intents:
            return 0
        hay = " ".join([
            getattr(paint, "features", "") or "",
            getattr(paint, "nome", "") or "",
        ]).lower()

        intent_terms = {
            "lavavel": ["lavável", "lavavel", "limp"],
            "antimofo": ["anti-mofo", "antimofo", "mofo", "umidade"],
            "sem_odor": ["sem odor", "sem cheiro", "baixo odor", "pouco cheiro"],
            "cobertura": ["cobertura", "rende", "rendimento"],
            "resistencia": ["resistente", "durável", "duravel", "proteção", "protecao"],
            "clima": ["uv", "sol", "chuva", "tempo", "intemper"],
        }

        score = 0
        for intent in intents:
            terms = intent_terms.get(intent) or []
            if any(term in hay for term in terms):
                score += 1
        return score

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
<<<<<<< HEAD
            response = "No momento, não encontrei tintas cadastradas no catálogo."
        else:
            response = "Aqui estão as tintas do catálogo:\n\n" + "\n".join(lines)
=======
            response = self.prompts.get('no_catalog', "No momento, não encontrei tintas cadastradas no catálogo.")
        else:
            catalog_header = self.prompts.get('catalog_header', "Aqui estão as tintas do catálogo:")
            response = f"{catalog_header}\n\n" + "\n".join(lines)
>>>>>>> feature/front-configs
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
        is_follow_up = self._is_follow_up(user_input)
        # Se não é follow-up, evite usar histórico/slots antigos na extração (reduz "vazamento" de contexto).
        extraction_history = self.conversation_memory if is_follow_up else [{"role": "user", "content": user_input}]
        slots_for_extraction = self.slot_memory if is_follow_up else PaintContext()
        context = self._extract_context(user_input, extraction_history, slots_for_extraction)

        if is_follow_up:
            # Merge de slots: mantém memória do que já foi definido antes
            merged = PaintContext(
                environment=context.environment or self.slot_memory.environment,
                surface_type=context.surface_type or self.slot_memory.surface_type,
                color=context.color or self.slot_memory.color,
                finish_type=context.finish_type or self.slot_memory.finish_type,
            )
        else:
            # Novo pedido: usar o que o usuário trouxe AGORA (sem herdar madeira/etc.).
            merged = PaintContext(
                environment=context.environment,
                surface_type=context.surface_type,
                color=context.color,
                finish_type=context.finish_type,
            )
            # Inferir interno/parede para ambientes típicos (ex.: escritório), se ainda estiver faltando.
            inferred = self._infer_room_context(user_input)
            merged = PaintContext(
                environment=merged.environment or inferred.environment,
                surface_type=merged.surface_type or inferred.surface_type,
                color=merged.color,
                finish_type=merged.finish_type,
            )

        # Inferência adicional segura (só preenche o que estiver faltando).
        # Ex.: "fachada" -> externo, "quarto" -> interno.
        inferred2 = self._infer_room_context(user_input)
        merged = PaintContext(
            environment=merged.environment or inferred2.environment,
            surface_type=merged.surface_type or inferred2.surface_type,
            color=merged.color,
            finish_type=merged.finish_type,
        )

        # Normalização de superfície (ex.: "fachada" -> "parede") antes de consultar DB/RAG.
        normalized_surface = self._normalize_surface_type(merged.surface_type, user_input=user_input)
        merged = PaintContext(
            environment=merged.environment,
            surface_type=normalized_surface,
            color=merged.color,
            finish_type=merged.finish_type,
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
        # Só interromper para perguntar quando NÃO há pistas suficientes para recomendar.
        # Ex.: "qual tinta você indica?" (sem ambiente, sem superfície, sem cor).
        #
        # Importante: se o usuário já trouxe uma pista forte (ex.: "madeira", "metal"),
        # NÃO devemos travar perguntando ambiente; os especialistas conseguem recomendar
        # mesmo com ambiente indefinido, e a pergunta pode vir no final para refinamento.
        if not merged.environment and not merged.surface_type and not merged.color:
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
        feature_intents = self._extract_feature_intents(user_input)
        all_paints = []
        for rec in specialist_recommendations:
            all_paints.extend(rec.recommended_paints)
        
        seen_ids = set()
        unique_paints = [p for p in all_paints if not (p.id in seen_ids or seen_ids.add(p.id))]
        if feature_intents and unique_paints:
            unique_paints.sort(key=lambda p: self._score_paint_by_intents(p, feature_intents), reverse=True)
            tools_used.append({"tool": "feature_intent_rank", "input": f"intents={feature_intents}"})
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

        # Se ainda não há produto, NÃO chamar LLM (evita alucinação de catálogo).
        # Responder de forma determinística e consultiva, pedindo o mínimo necessário
        # para encontrar um item real no banco.
        if best_paint is None:
            missing_now = self._get_missing_slots(merged)
            if not merged.environment:
                response_text = self._ask_for_missing(missing_now)
            else:
                env_label = merged.environment
                surf = (merged.surface_type or "").strip().lower()
                cor = (merged.color or "").strip().lower()
<<<<<<< HEAD

                # Nunca assumir "madeira" (isso estava puxando respostas erradas).
                if not surf:
                    cor_hint = f" na cor {cor}" if cor else ""
                    response_text = (
                        f"No catálogo atual, não encontrei uma tinta cadastrada com esses critérios para ambiente {env_label}{cor_hint}. "
                        f"Você vai pintar **parede**, **madeira** ou **metal**?"
                    )
                elif any(k in surf for k in ["madeira", "mdf", "compens", "laminad"]):
                    # Madeira: pergunta certa depende do ambiente
                    if env_label == "externo":
                        response_text = (
                            "No catálogo atual, não encontrei uma tinta cadastrada especificamente para madeira em área externa. "
                            "A madeira é crua ou já tem verniz/tinta, e pega sol/chuva diretamente?"
                        )
                    else:
                        response_text = (
                            "No catálogo atual, não encontrei uma tinta cadastrada especificamente para madeira em ambiente interno. "
                            "A madeira é crua ou já tem verniz/tinta, e você quer acabamento fosco ou acetinado?"
                        )
                elif any(k in surf for k in ["metal", "ferro", "aço", "aco", "alum", "inox"]):
                    response_text = (
                        f"No catálogo atual, não encontrei uma tinta cadastrada especificamente para {merged.surface_type} em ambiente {env_label}. "
                        "É metal novo ou já pintado (com ferrugem/descascando)?"
                    )
                else:
                    # Parede/alvenaria/etc.
                    cor_hint = f" na cor {cor}" if cor else ""
                    response_text = (
                        f"No catálogo atual, não encontrei uma tinta cadastrada especificamente para {merged.surface_type} em ambiente {env_label}{cor_hint}. "
                        "A parede é gesso/massa corrida ou reboco, e você prefere fosco ou acetinado?"
                    )
=======
                cor_hint = f" na cor {cor}" if cor else ""

                no_product = self.prompts.get('no_product_responses', {})

                # Nunca assumir "madeira" (isso estava puxando respostas erradas).
                if not surf:
                    template = no_product.get('no_environment_and_surface', 
                        "No catálogo atual, não encontrei uma tinta cadastrada com esses critérios para ambiente {env_label}{cor_hint}. Você vai pintar **parede**, **madeira** ou **metal**?")
                    response_text = template.format(env_label=env_label, cor_hint=cor_hint)
                elif any(k in surf for k in ["madeira", "mdf", "compens", "laminad"]):
                    # Madeira: pergunta certa depende do ambiente
                    if env_label == "externo":
                        response_text = no_product.get('madeira_externa',
                            "No catálogo atual, não encontrei uma tinta cadastrada especificamente para madeira em área externa. A madeira é crua ou já tem verniz/tinta, e pega sol/chuva diretamente?")
                    else:
                        response_text = no_product.get('madeira_interna',
                            "No catálogo atual, não encontrei uma tinta cadastrada especificamente para madeira em ambiente interno. A madeira é crua ou já tem verniz/tinta, e você quer acabamento fosco ou acetinado?")
                elif any(k in surf for k in ["metal", "ferro", "aço", "aco", "alum", "inox"]):
                    template = no_product.get('metal',
                        "No catálogo atual, não encontrei uma tinta cadastrada especificamente para {surface_type} em ambiente {env_label}. É metal novo ou já pintado (com ferrugem/descascando)?")
                    response_text = template.format(surface_type=merged.surface_type, env_label=env_label)
                else:
                    # Parede/alvenaria/etc.
                    template = no_product.get('parede',
                        "No catálogo atual, não encontrei uma tinta cadastrada especificamente para {surface_type} em ambiente {env_label}{cor_hint}. A parede é gesso/massa corrida ou reboco, e você prefere fosco ou acetinado?")
                    response_text = template.format(surface_type=merged.surface_type, env_label=env_label, cor_hint=cor_hint)
>>>>>>> feature/front-configs

            tools_used.append({
                "tool": "db_catalog_no_match",
                "input": f"environment={merged.environment} surface_type={merged.surface_type} color={merged.color} finish_type={merged.finish_type}"
            })
            self.conversation_memory.append({"role": "assistant", "content": response_text})
            return {
                "response": response_text,
                "context": context_dict,
                "paints_mentioned": [],
                "tools_used": tools_used,
                "specialists_consulted": [{"specialist": r.specialist_name, "confidence": r.confidence} for r in specialist_recommendations],
                "reasoning_chain": [r.to_dict() for r in specialist_recommendations],
                "metadata": {"execution_time_ms": (time.time() - start_time) * 1000},
            }

        # 5. Prompt de Síntese Final (O Coração da Humanização)
        specialist_insights = "\n".join([f"- {r.specialist_name}: {r.reasoning}" for r in specialist_recommendations])
        
        paint_info = self._format_paint_info(best_paint)

<<<<<<< HEAD
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
            REGRA CRÍTICA: Você só pode mencionar o produto que está em "DADOS DO PRODUTO SELECIONADO". Não invente nem cite outros nomes de produtos.
            Não finalize com perguntas.
            Responda APENAS com o texto final ao usuário (sem cabeçalhos, sem JSON, sem repetir seções acima).
            
            RESPOSTA DO CONSULTOR:
        """)
=======
        final_synthesis_template = self.prompts.get('final_synthesis', '')
        prompt = ChatPromptTemplate.from_template(final_synthesis_template)
>>>>>>> feature/front-configs
        
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

<<<<<<< HEAD
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
=======
        context_extraction_template = self.prompts.get('context_extraction', '')
        prompt = ChatPromptTemplate.from_template(context_extraction_template)
        
>>>>>>> feature/front-configs
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
<<<<<<< HEAD
        questions = {
            "ambiente (interno/externo)": "Para te indicar a melhor tecnologia, esse ambiente é interno ou externo?",
            "tipo de superfície": "Em qual superfície faremos a aplicação (parede, madeira ou metal)?"
        }
        return questions.get(missing[0], "Poderia me dar mais detalhes sobre o que você deseja transformar?")
=======
        questions = self.prompts.get('missing_slot_questions', {})
        
        slot_map = {
            "ambiente (interno/externo)": "ambiente",
            "tipo de superfície": "tipo_de_superficie"
        }
        
        if not missing:
            return questions.get('default', "Poderia me dar mais detalhes sobre o que você deseja transformar?")
        
        slot_key = slot_map.get(missing[0], 'default')
        return questions.get(slot_key, questions.get('default', "Poderia me dar mais detalhes sobre o que você deseja transformar?"))
>>>>>>> feature/front-configs

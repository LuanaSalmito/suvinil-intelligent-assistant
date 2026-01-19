from typing import Dict
from sqlalchemy.orm import Session
from app.ai.rag_service import RagService
from app.ai.specialists import ALL_SPECIALISTS
from app.ai.agent_service import AgentService
from app.models.paint import Environment


class Orchestrator:
    """
    Agente Orquestrador conforme o PDF.
    """

    def __init__(self):
        self.rag_service = RagService()
        self.agent_service = AgentService()
        self.specialists = ALL_SPECIALISTS

    def handle(
        self,
        db: Session,
        user_id: int,
        message: str
    ):
        slots = self._extract_slots(message)

        # 1️⃣ Especialistas primeiro
        for specialist in self.specialists:
            if specialist.can_handle(slots):
                result = specialist.consult(slots)

                if result.get("needs_more_info"):
                    return self.agent_service.respond(
                        db,
                        user_id,
                        message,
                        result["reasoning"]
                    )

        # 2️⃣ RAG obrigatório
        paints = self.rag_service.search_paints(db, slots)

        if not paints:
            return self.agent_service.respond(
                db,
                user_id,
                message,
                "Não encontrei uma tinta adequada. Pode me dar mais detalhes?"
            )

        selected = paints[0]

        # 3️⃣ LLM apenas escreve (sem decidir)
        response = self._format_response(selected)

        return self.agent_service.respond(
            db,
            user_id,
            message,
            response
        )

    def _extract_slots(self, text: str) -> Dict:
        text = text.lower()
        slots = {}

        if "extern" in text or "fachada" in text:
            slots["environment"] = Environment.EXTERIOR.value

        if "intern" in text or "quarto" in text:
            slots["environment"] = Environment.INTERIOR.value

        if "madeira" in text:
            slots["surface_type"] = "madeira"

        if "lavável" in text or "limpar" in text:
            slots["feature"] = "lavável"

        if "sem cheiro" in text or "odor" in text:
            slots["feature"] = "sem odor"

        return slots

    def _format_response(self, paint) -> str:
        features = paint.features or ""

        return (
            f"Recomendo a **{paint.name}**, indicada para ambiente "
            f"{paint.environment.value} em {paint.surface_type}. "
            f"Possui acabamento {paint.finish_type.value} e recursos como "
            f"{features}."
        )

"""
Serviço RAG (Retrieval-Augmented Generation) para busca semântica de tintas.

Funcionalidades:
- Indexação de tintas em ChromaDB
- Busca semântica com embeddings OpenAI
- Filtros por ambiente e acabamento
- Geração de respostas conversacionais e amigáveis para chat
"""

import os
import logging
import shutil
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage

from app.repositories.paint_repository import PaintRepository
from app.core.config import settings


logger = logging.getLogger(__name__)


class RAGService:
    """
    Serviço de RAG para recomendação e busca semântica de tintas.

    Combina:
    - Embeddings OpenAI
    - ChromaDB
    - LLM para respostas naturais em chat
    """

    PERSIST_DIRECTORY = "./chroma_db"
    COLLECTION_NAME = "suvinil_paints"

    def __init__(self, db: Session):
        self.db = db

        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small",
        )

        self.vectorstore: Optional[Chroma] = None
        self._initialize_vectorstore()

    # ---------------------------------------------------------------------
    # INDEXAÇÃO
    # ---------------------------------------------------------------------

    def _paint_to_document(self, paint) -> Document:
        """Converte uma tinta do banco em Document para indexação."""

        features_list = paint.features.split(",") if paint.features else []
        features_text = ", ".join(f.strip() for f in features_list)

        text = f"""
Produto: {paint.name}
Cor: {paint.color_name or paint.color or "Não especificada"}

AMBIENTE DE USO:
- Tipo: {paint.environment.value}
- Superfície: {paint.surface_type or "Diversas superfícies"}

ESPECIFICAÇÕES:
- Acabamento: {paint.finish_type.value}
- Linha: {paint.line.value}
- Preço aproximado: R$ {paint.price:.2f}

BENEFÍCIOS:
{features_text if features_text else "Boa cobertura, durabilidade e acabamento uniforme."}

DESCRIÇÃO:
{paint.description or "Tinta Suvinil de alta qualidade."}

PALAVRAS-CHAVE:
{paint.name}, {paint.color_name or ""}, {paint.environment.value},
{paint.finish_type.value}, {features_text}
""".strip()

        metadata = {
            "paint_id": paint.id,
            "name": paint.name,
            "color": paint.color_name or paint.color or "",
            "color_hex": paint.color or "",
            "environment": paint.environment.value,
            "finish_type": paint.finish_type.value,
            "line": paint.line.value,
            "surface_type": paint.surface_type or "",
            "features": paint.features or "",
            "price": paint.price or 0,
        }

        return Document(page_content=text, metadata=metadata)

    def _initialize_vectorstore(self):
        """Cria ou recria o vector store com dados atualizados."""

        logger.info("Inicializando vector store de tintas...")

        try:
            paints = PaintRepository.get_all(self.db, skip=0, limit=1000)

            if not paints:
                logger.warning("Nenhuma tinta encontrada para indexação.")
                return

            documents = [self._paint_to_document(p) for p in paints]

            if os.path.exists(self.PERSIST_DIRECTORY):
                shutil.rmtree(self.PERSIST_DIRECTORY, ignore_errors=True)

            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.PERSIST_DIRECTORY,
                collection_name=self.COLLECTION_NAME,
            )

            logger.info(f"Vector store criado com {len(documents)} tintas.")

        except Exception as e:
            logger.error(f"Erro ao criar vector store: {e}")

            if os.path.exists(self.PERSIST_DIRECTORY):
                try:
                    self.vectorstore = Chroma(
                        persist_directory=self.PERSIST_DIRECTORY,
                        embedding_function=self.embeddings,
                        collection_name=self.COLLECTION_NAME,
                    )
                    logger.info("Vector store carregado do disco como fallback.")
                except Exception as e2:
                    logger.error(f"Falha ao carregar vector store: {e2}")

    # ---------------------------------------------------------------------
    # BUSCA
    # ---------------------------------------------------------------------

    def search_paints(
        self,
        query: str,
        k: int = 5,
        filter_environment: Optional[str] = None,
        filter_finish: Optional[str] = None,
    ) -> List[Dict[str, Any]]:

        if not self.vectorstore:
            logger.warning("Vector store indisponível.")
            return []

        where_filter = None
        if filter_environment or filter_finish:
            where_filter = {}
            if filter_environment:
                where_filter["environment"] = filter_environment
            if filter_finish:
                where_filter["finish_type"] = filter_finish

        try:
            if where_filter:
                results = self.vectorstore.similarity_search_with_score(
                    query, k=k, filter=where_filter
                )
            else:
                results = self.vectorstore.similarity_search_with_score(query, k=k)

            paints = []
            seen_ids = set()

            for doc, score in results:
                paint_id = doc.metadata.get("paint_id")

                if paint_id in seen_ids:
                    continue

                seen_ids.add(paint_id)

                paints.append({
                    **doc.metadata,
                    "content": doc.page_content,
                    "similarity_score": float(score),
                })

            return paints

        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            return []

    # ---------------------------------------------------------------------
    # CONTEXTO PARA CHAT
    # ---------------------------------------------------------------------

    def _paint_context_snippet(self, paint: Dict[str, Any]) -> str:
        """Resumo curto e amigável de uma tinta para uso no prompt."""

        return f"""
Produto: {paint['name']}
Cor: {paint['color'] or 'Não especificada'}
Ambiente indicado: {paint['environment']}
Acabamento: {paint['finish_type']}
Linha: {paint['line']}
Preço aproximado: R$ {paint['price']}

Principais benefícios:
{paint['features'] or 'Boa cobertura, acabamento bonito e fácil manutenção.'}
""".strip()

    # ---------------------------------------------------------------------
    # RESPOSTA CONVERSACIONAL (CHAT)
    # ---------------------------------------------------------------------

    def answer_query(
        self,
        query: str,
        k: int = 5,
        filter_environment: Optional[str] = None,
        filter_finish: Optional[str] = None,
    ) -> str:
        """
        Responde perguntas do usuário de forma natural e amigável,
        usando RAG + LLM.
        """

        results = self.search_paints(
            query=query,
            k=k,
            filter_environment=filter_environment,
            filter_finish=filter_finish,
        )

        if not results:
            return (
                "Não encontrei uma tinta perfeita com base no que você descreveu, "
                "mas posso te ajudar se quiser ajustar a busca ou me contar um pouco mais 😊"
            )

        context = "\n\n---\n\n".join(
            self._paint_context_snippet(p) for p in results
        )

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        system_prompt = """
Você é um consultor especialista em tintas Suvinil.

Seu tom deve ser:
- Amigável
- Natural
- Claro
- Próximo do cliente

Explique as opções como se estivesse ajudando alguém dentro de uma loja.
Evite listas técnicas e linguagem robótica.

Sempre finalize convidando o cliente a continuar a conversa.
"""

        user_prompt = f"""
Pergunta do cliente:
"{query}"

Use as opções abaixo para responder de forma clara e acolhedora.

Opções disponíveis:
{context}
"""

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        return response.content

    # ---------------------------------------------------------------------
    # UTILIDADES
    # ---------------------------------------------------------------------

    def get_similar_paints(self, paint_id: int, k: int = 3) -> List[Dict[str, Any]]:
        paint = PaintRepository.get_by_id(self.db, paint_id)
        if not paint:
            return []

        query = f"{paint.name} {paint.environment.value} {paint.finish_type.value}"
        results = self.search_paints(query, k=k + 1)

        return [r for r in results if r["paint_id"] != paint_id][:k]

    def reindex(self):
        """Força reindexação completa."""
        logger.info("Reindexando vector store manualmente...")
        self._initialize_vectorstore()

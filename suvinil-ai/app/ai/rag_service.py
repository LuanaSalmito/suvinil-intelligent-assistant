import os
# ChromaDB telemetria (anônima) pode falhar em alguns ambientes/versões e poluir logs.
# Desabilitar aqui garante que esteja setado antes de importar/instanciar o Chroma.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY", "False")
import logging
import shutil
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.repositories.paint_repository import PaintRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    PERSIST_DIRECTORY = "./chroma_db"
    COLLECTION_NAME = "suvinil_paints_v2"
    # Retrocompatibilidade com coleções antigas
    LEGACY_COLLECTION_NAME = "suvinil_paints"

    def __init__(self, db: Session):
        self.db = db
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL,
        )
        self.vectorstore: Optional[Chroma] = None
        self._initialize_vectorstore()

    def _paint_to_document(self, paint) -> Document:
        content = (
            f"Produto: {paint.nome}. Ambiente: {paint.ambiente.value}. "
            f"Superfície: {paint.tipo_parede}. Acabamento: {paint.acabamento.value}. "
            f"Cor: {paint.cor}. Destaques: {paint.features}. Linha: {paint.linha.value}."
        )
        metadata = {
            "paint_id": paint.id,
            "nome": paint.nome,
            "cor": (paint.cor or "").lower(),
            "ambiente": paint.ambiente.value.lower(),
            "tipo_parede": (paint.tipo_parede or "").lower(),
            "linha": paint.linha.value
        }
        return Document(page_content=content, metadata=metadata)

    def _initialize_vectorstore(self):
        if os.path.exists(self.PERSIST_DIRECTORY):
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.PERSIST_DIRECTORY,
                    embedding_function=self.embeddings,
                    collection_name=self.COLLECTION_NAME,
                )
                return
            except Exception as e:
                logger.warning(f"Falha ao carregar coleção {self.COLLECTION_NAME}: {e}")
                try:
                    self.vectorstore = Chroma(
                        persist_directory=self.PERSIST_DIRECTORY,
                        embedding_function=self.embeddings,
                        collection_name=self.LEGACY_COLLECTION_NAME,
                    )
                    return
                except Exception as e2:
                    logger.error(f"Falha ao carregar coleção legacy {self.LEGACY_COLLECTION_NAME}: {e2}")

        # Se não existe ou falhou, reindexar
        self.reindex()

    def reindex(self) -> int:
        """Recria o índice do zero a partir do catálogo no SQL."""
        logger.info("Reindexando banco de vetores (Chroma)...")
        paints = PaintRepository.get_all(self.db, skip=0, limit=2000)
        if not paints:
            self.vectorstore = None
            return 0

        documents = [self._paint_to_document(p) for p in paints]

        if os.path.exists(self.PERSIST_DIRECTORY):
            shutil.rmtree(self.PERSIST_DIRECTORY, ignore_errors=True)

        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.PERSIST_DIRECTORY,
            collection_name=self.COLLECTION_NAME,
        )
        return len(documents)

    def search_paints(self, query: str, k: int = 3, filters: Dict = None) -> List[Dict]:
        if not self.vectorstore: return []
        
        conditions = []
        if filters:
            if filters.get("ambiente"): conditions.append({"ambiente": filters["ambiente"].lower()})
            if filters.get("cor"): conditions.append({"cor": filters["cor"].lower()})
            if filters.get("tipo_parede"): conditions.append({"tipo_parede": filters["tipo_parede"].lower()})

        where_clause = {"$and": conditions} if len(conditions) > 1 else (conditions[0] if conditions else None)
        results = self.vectorstore.similarity_search_with_score(query, k=k, filter=where_clause)
        return [{**doc.metadata, "content": doc.page_content, "score": score} for doc, score in results]

    def get_technical_context(self, query: str, filters: Dict = None) -> str:
        results = self.search_paints(query, k=1, filters=filters)
        if not results: return "Nenhum produto encontrado com estes critérios específicos."
        p = results[0]
        return f"Produto: {p['nome']} | Cor: {p['cor']} | Linha: {p['linha']} | Características: {p['content']}"

    def answer_with_context(self, query: str, filters: Dict = None) -> str:
        """
        Alias retrocompatível (código antigo chamava answer_with_context).
        """
        return self.get_technical_context(query, filters)
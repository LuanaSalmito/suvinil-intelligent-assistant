"""Serviço RAG (Retrieval-Augmented Generation)"""
from typing import List, Optional
from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.repositories.paint_repository import PaintRepository
from app.core.config import settings
import os


class RAGService:
    """Serviço para RAG - busca informações sobre tintas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Inicializa vectorstore com tintas"""
        # Buscar todas as tintas
        paints = PaintRepository.get_all(self.db, skip=0, limit=1000)
        
        # Criar documentos
        documents = []
        for paint in paints:
            doc_text = self._paint_to_text(paint)
            documents.append(Document(
                page_content=doc_text,
                metadata={
                    "paint_id": paint.id,
                    "name": paint.name,
                    "color": paint.color_name or paint.color or "",
                    "environment": paint.environment.value,
                    "finish_type": paint.finish_type.value,
                    "line": paint.line.value,
                }
            ))
        
        # Criar ou carregar vectorstore
        persist_directory = "./chroma_db"
        if documents:
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
            )
            splits = text_splitter.split_documents(documents)
            
            # Criar vectorstore
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=persist_directory,
            )
        else:
            # Carregar vectorstore existente
            if os.path.exists(persist_directory):
                self.vectorstore = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embeddings,
                )
    
    def _paint_to_text(self, paint) -> str:
        """Converte tinta em texto para embedding"""
        features_list = paint.features.split(",") if paint.features else []
        features_text = ", ".join([f.strip() for f in features_list])
        
        text = f"""
Nome: {paint.name}
Cor: {paint.color_name or paint.color or "Não especificada"}
Tipo de superfície: {paint.surface_type or "Não especificado"}
Ambiente: {paint.environment.value}
Tipo de acabamento: {paint.finish_type.value}
Linha: {paint.line.value}
Features: {features_text if features_text else "Nenhuma"}
Descrição: {paint.description or "Não disponível"}
Preço: R$ {paint.price or "Não disponível"}
        """.strip()
        
        return text
    
    def search_paints(self, query: str, k: int = 5) -> List[dict]:
        """Busca tintas relevantes usando embedding"""
        if not self.vectorstore:
            return []
        
        # Buscar documentos similares
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        paints_data = []
        for doc, score in results:
            metadata = doc.metadata
            paints_data.append({
                "paint_id": metadata.get("paint_id"),
                "name": metadata.get("name"),
                "color": metadata.get("color"),
                "environment": metadata.get("environment"),
                "finish_type": metadata.get("finish_type"),
                "line": metadata.get("line"),
                "content": doc.page_content,
                "score": float(score),
            })
        
        return paints_data

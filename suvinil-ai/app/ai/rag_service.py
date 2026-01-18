"""
Serviço RAG (Retrieval-Augmented Generation) para busca semântica de tintas.

Este módulo implementa:
- Indexação de tintas em vector store (ChromaDB)
- Busca semântica usando embeddings OpenAI
- Cache e re-indexação automática
"""
import os
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.repositories.paint_repository import PaintRepository
from app.core.config import settings

# Configurar logging
logger = logging.getLogger(__name__)


class RAGService:
    """
    Serviço para RAG - Busca semântica de informações sobre tintas.
    
    Usa embeddings OpenAI + ChromaDB para busca por similaridade.
    """
    
    # Diretório para persistir o vector store
    PERSIST_DIRECTORY = "./chroma_db"
    
    # Nome da coleção
    COLLECTION_NAME = "suvinil_paints"
    
    def __init__(self, db: Session):
        self.db = db
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"  # Modelo mais recente e eficiente
        )
        self.vectorstore: Optional[Chroma] = None
        self._initialize_vectorstore()
    
    def _paint_to_document(self, paint) -> Document:
        """
        Converte uma tinta em um Document para indexação.
        
        O texto é estruturado para otimizar a busca semântica.
        """
        # Processar features
        features_list = paint.features.split(",") if paint.features else []
        features_text = ", ".join([f.strip() for f in features_list])
        
        # Criar texto rico para embedding
        text = f"""
Produto: {paint.name}
Cor: {paint.color_name or paint.color or "Não especificada"}

AMBIENTE DE USO:
- Tipo: {paint.environment.value}
- Superfície: {paint.surface_type or "Múltiplas superfícies"}

ESPECIFICAÇÕES TÉCNICAS:
- Acabamento: {paint.finish_type.value}
- Linha: {paint.line.value}
- Preço: R$ {paint.price:.2f} (referência)

CARACTERÍSTICAS E BENEFÍCIOS:
{features_text if features_text else "Características padrão"}

DESCRIÇÃO:
{paint.description or "Tinta de qualidade Suvinil."}

PALAVRAS-CHAVE: {paint.name}, {paint.color_name or ''}, {paint.environment.value}, {paint.finish_type.value}, {features_text}
        """.strip()
        
        # Metadados para filtragem
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
        """Inicializa ou atualiza o vector store com as tintas do banco."""
        logger.info("Inicializando vector store...")
        
        try:
            # Buscar todas as tintas ativas
            paints = PaintRepository.get_all(self.db, skip=0, limit=1000)
            
            if not paints:
                logger.warning("Nenhuma tinta encontrada no banco de dados")
                return
            
            # Criar documentos
            documents = [self._paint_to_document(paint) for paint in paints]
            
            logger.info(f"Indexando {len(documents)} tintas...")
            
            # Criar vector store
            # Limpar coleção existente para garantir dados atualizados
            if os.path.exists(self.PERSIST_DIRECTORY):
                try:
                    # Tentar deletar coleção existente
                    import shutil
                    shutil.rmtree(self.PERSIST_DIRECTORY, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Erro ao limpar vector store: {e}")
            
            # Criar nova coleção
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.PERSIST_DIRECTORY,
                collection_name=self.COLLECTION_NAME,
            )
            
            logger.info(f"Vector store inicializado com {len(documents)} documentos")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar vector store: {e}")
            # Tentar carregar existente como fallback
            if os.path.exists(self.PERSIST_DIRECTORY):
                try:
                    self.vectorstore = Chroma(
                        persist_directory=self.PERSIST_DIRECTORY,
                        embedding_function=self.embeddings,
                        collection_name=self.COLLECTION_NAME,
                    )
                    logger.info("Vector store carregado do disco")
                except Exception as e2:
                    logger.error(f"Falha ao carregar vector store: {e2}")
    
    def search_paints(
        self, 
        query: str, 
        k: int = 5,
        filter_environment: Optional[str] = None,
        filter_finish: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca tintas relevantes usando busca semântica.
        
        Args:
            query: Consulta em linguagem natural
            k: Número de resultados
            filter_environment: Filtrar por ambiente (opcional)
            filter_finish: Filtrar por acabamento (opcional)
        
        Returns:
            Lista de dicts com informações das tintas encontradas
        """
        if not self.vectorstore:
            logger.warning("Vector store não disponível")
            return []
        
        logger.info(f"Buscando: '{query}' (k={k})")
        
        try:
            # Preparar filtros
            where_filter = None
            if filter_environment or filter_finish:
                conditions = {}
                if filter_environment:
                    conditions["environment"] = filter_environment
                if filter_finish:
                    conditions["finish_type"] = filter_finish
                where_filter = conditions
            
            # Buscar documentos similares
            if where_filter:
                results = self.vectorstore.similarity_search_with_score(
                    query, 
                    k=k,
                    filter=where_filter
                )
            else:
                results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # Processar resultados
            paints_data = []
            seen_ids = set()  # Evitar duplicatas
            
            for doc, score in results:
                metadata = doc.metadata
                paint_id = metadata.get("paint_id")
                
                # Evitar duplicatas
                if paint_id in seen_ids:
                    continue
                seen_ids.add(paint_id)
                
                paints_data.append({
                    "paint_id": paint_id,
                    "name": metadata.get("name"),
                    "color": metadata.get("color"),
                    "color_hex": metadata.get("color_hex"),
                    "environment": metadata.get("environment"),
                    "finish_type": metadata.get("finish_type"),
                    "line": metadata.get("line"),
                    "surface_type": metadata.get("surface_type"),
                    "features": metadata.get("features"),
                    "price": metadata.get("price"),
                    "content": doc.page_content,
                    "similarity_score": float(score),
                })
            
            logger.info(f"Encontradas {len(paints_data)} tintas")
            return paints_data
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []
    
    def search_by_color(self, color: str, k: int = 5) -> List[Dict[str, Any]]:
        """Busca tintas por cor específica."""
        return self.search_paints(f"cor {color} tinta", k=k)
    
    def search_by_features(self, features: List[str], k: int = 5) -> List[Dict[str, Any]]:
        """Busca tintas por características."""
        features_query = " ".join(features)
        return self.search_paints(f"tinta {features_query}", k=k)
    
    def get_similar_paints(self, paint_id: int, k: int = 3) -> List[Dict[str, Any]]:
        """Encontra tintas similares a uma tinta específica."""
        # Buscar a tinta original
        paint = PaintRepository.get_by_id(self.db, paint_id)
        if not paint:
            return []
        
        # Criar query baseada na tinta
        query = f"{paint.name} {paint.color_name or ''} {paint.environment.value} {paint.finish_type.value}"
        
        # Buscar similares (k+1 para excluir a própria tinta)
        results = self.search_paints(query, k=k+1)
        
        # Remover a própria tinta dos resultados
        return [r for r in results if r.get("paint_id") != paint_id][:k]
    
    def reindex(self):
        """Força re-indexação do vector store."""
        logger.info("Forçando re-indexação do vector store...")
        self._initialize_vectorstore()


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
            # Processar features para metadados (para busca mais precisa)
            features_list = []
            features_lower = []
            if paint.features:
                raw_features = [f.strip() for f in paint.features.split(",") if f.strip()]
                features_list = raw_features
                features_lower = [f.lower() for f in raw_features]
            
            documents.append(Document(
                page_content=doc_text,
                metadata={
                    "paint_id": paint.id,
                    "name": paint.name,
                    "color": paint.color_name or paint.color or "",
                    "environment": paint.environment.value,
                    "finish_type": paint.finish_type.value,
                    "line": paint.line.value,
                    "features": paint.features or "",  # Features originais como string
                    "features_normalized": ", ".join(features_lower) if features_lower else "",  # Features normalizadas para busca
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
        """Converte tinta em texto rico para embedding com features destacadas"""
        # Processar features de forma mais rica para busca semântica
        features_list = []
        if paint.features:
            # Dividir por vírgula e processar cada feature
            raw_features = [f.strip() for f in paint.features.split(",") if f.strip()]
            for feature in raw_features:
                feature_lower = feature.lower()
                # Criar frases descritivas para cada feature (melhor para embeddings)
                if "anti-mofo" in feature_lower or "antimofo" in feature_lower:
                    features_list.append("Esta tinta possui proteção anti-mofo e previne o aparecimento de fungos.")
                elif "sem odor" in feature_lower or "sem cheiro" in feature_lower:
                    features_list.append("Esta tinta é formulada sem odor, ideal para ambientes onde o cheiro é inconveniente.")
                elif "lavável" in feature_lower:
                    features_list.append("Esta tinta é lavável e resistente à limpeza com água e sabão.")
                elif "proteção uv" in feature_lower or "uv" in feature_lower:
                    features_list.append("Esta tinta oferece proteção contra raios ultravioleta do sol.")
                elif "impermeável" in feature_lower:
                    features_list.append("Esta tinta é impermeável e resistente à água.")
                elif "resistente" in feature_lower:
                    if "chuva" in feature_lower:
                        features_list.append("Esta tinta é resistente à chuva e à umidade.")
                    elif "calor" in feature_lower:
                        features_list.append("Esta tinta é resistente ao calor e a altas temperaturas.")
                    elif "tempo" in feature_lower or "intemperismo" in feature_lower:
                        features_list.append("Esta tinta é resistente ao tempo e ao intemperismo.")
                    else:
                        features_list.append(f"Esta tinta possui {feature}, uma característica de resistência.")
                elif "cobertura" in feature_lower:
                    features_list.append("Esta tinta possui alta cobertura e rendimento.")
                else:
                    # Para features não mapeadas, criar frase descritiva genérica
                    features_list.append(f"Esta tinta possui {feature} como característica especial.")
        
        # Criar seção de features estruturada
        features_section = ""
        if features_list:
            features_section = "Características especiais:\n" + "\n".join(f"  - {f}" for f in features_list)
        else:
            features_section = "Características especiais: Nenhuma característica especial."
        
        # Texto estruturado e rico para melhor embedding semântico
        text = f"""
Tinta: {paint.name}

Informações básicas:
- Cor: {paint.color_name or paint.color or "Não especificada"}
- Tipo de superfície: {paint.surface_type or "Não especificado"}
- Ambiente de uso: {paint.environment.value}
- Tipo de acabamento: {paint.finish_type.value}
- Linha de produto: {paint.line.value}
- Preço: R$ {paint.price or "Não disponível"}

{features_section}

Descrição detalhada: {paint.description or "Descrição não disponível."}

Esta tinta é adequada para {paint.environment.value} e possui acabamento {paint.finish_type.value}.
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

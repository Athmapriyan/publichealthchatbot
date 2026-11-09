"""
RAG retrieval layer: embeds the trusted disease knowledge base into ChromaDB
and retrieves relevant chunks for a query, with a similarity-score threshold
so the system can refuse rather than hallucinate when evidence is weak.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.utils import embedding_functions

from backend.config import settings

logger = logging.getLogger("rag.retriever")

COLLECTION_NAME = "health_knowledge_base"


class HealthKnowledgeRetriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        if self.collection.count() == 0:
            self._ingest_knowledge_base()

    def _ingest_knowledge_base(self):
        path = Path(settings.KNOWLEDGE_BASE_PATH)
        if not path.exists():
            logger.warning("Knowledge base file not found at %s; retriever will be empty.", path)
            return
        docs = json.loads(path.read_text(encoding="utf-8"))
        ids, texts, metadatas = [], [], []
        for d in docs:
            ids.append(d["id"])
            texts.append(d["content"])
            metadatas.append({
                "disease": d.get("disease", ""),
                "document_type": d.get("document_type", ""),
                "source": d.get("source", ""),
                "publisher": d.get("publisher", ""),
                "publication_date": d.get("publication_date", ""),
                "language": d.get("language", "en"),
                "url": d.get("url", ""),
            })
        self.collection.add(ids=ids, documents=texts, metadatas=metadatas)
        logger.info("Ingested %d knowledge base documents into Chroma.", len(ids))

    def retrieve(self, query: str, top_k: int = None, disease_filter: str = None) -> List[Dict[str, Any]]:
        """Return relevant chunks with metadata and similarity score.
        Chunks below RAG_SCORE_THRESHOLD are dropped so the caller can detect
        'insufficient evidence' and refuse rather than hallucinate.
        """
        top_k = top_k or settings.RAG_TOP_K
        where = {"disease": disease_filter} if disease_filter else None
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
        )
        chunks = []
        if not results["ids"] or not results["ids"][0]:
            return chunks
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]  # cosine distance (lower = closer)
            similarity = 1 - distance
            if similarity < settings.RAG_SCORE_THRESHOLD:
                continue
            chunks.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": round(similarity, 3),
            })
        return chunks


# Lazy singleton so importing this module doesn't immediately load the embedding model
_retriever_instance: HealthKnowledgeRetriever | None = None


def get_retriever() -> HealthKnowledgeRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HealthKnowledgeRetriever()
    return _retriever_instance

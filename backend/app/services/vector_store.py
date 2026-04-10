import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import hashlib
import os
import logging

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self):
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")

        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name="questions",
            metadata={"description": "Interview questions vector store"}
        )
        logger.info("Vector store initialized")

    def add_question(self, question_id: str, content: str, metadata: Dict):
        import threading

        def async_add():
            try:
                embedding_id = hashlib.md5(question_id.encode()).hexdigest()
                self.collection.add(
                    ids=[embedding_id],
                    documents=[content],
                    metadatas=[{**metadata, "question_id": question_id}]
                )
            except Exception as e:
                logger.error(f"Failed to add question to vector store: {e}")

        thread = threading.Thread(target=async_add, daemon=True)
        thread.start()

    def search_similar_questions(self, query: str, n_results: int = 5, threshold: float = 0.7):
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2
            )

            similar_questions = []
            if results['ids'] and results['ids'][0]:
                for i, (doc_id, doc, meta, distance) in enumerate(zip(
                        results['ids'][0],
                        results['documents'][0],
                        results['metadatas'][0],
                        results['distances'][0]
                )):
                    similarity = 1 - distance
                    if similarity >= threshold:
                        similar_questions.append({
                            "id": meta.get("question_id", doc_id),
                            "content": doc,
                            "similarity": round(similarity, 3),
                            "metadata": meta
                        })

            return similar_questions[:n_results]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def delete_question(self, question_id: str):
        embedding_id = hashlib.md5(question_id.encode()).hexdigest()
        try:
            self.collection.delete(ids=[embedding_id])
        except Exception as e:
            logger.error(f"Failed to delete question: {e}")


vector_store = VectorStoreService()

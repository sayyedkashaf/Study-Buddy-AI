"""
Vector Store — ChromaDB wrapper for semantic search and RAG.

Uses ChromaDB's built-in embedding function (all-MiniLM-L6-v2)
so there are zero external API costs for embeddings.
"""

import os
import logging
from pathlib import Path
from datetime import datetime, timezone

import chromadb

from api.core.config import CHROMA_PATH

logger = logging.getLogger(__name__)


class VectorStore:
    """Persistent ChromaDB vector store for syllabus documents and conversations."""

    _instances: dict = {}

    def __new__(cls, chroma_path: str = None):
        target_path = str(chroma_path or os.getenv("CHROMA_PATH", CHROMA_PATH))
        if target_path not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[target_path] = instance
        return cls._instances[target_path]

    def __init__(self, chroma_path: str = None):
        target_path = str(chroma_path or os.getenv("CHROMA_PATH", CHROMA_PATH))
        if getattr(self, "_initialized", False):
            return

        self.chroma_path = target_path
        Path(target_path).mkdir(parents=True, exist_ok=True)
        try:
            logger.info(f"Initializing ChromaDB client at {target_path}")
            self.client = chromadb.PersistentClient(path=target_path)
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}", exc_info=True)
            raise

        # Collection for syllabus documents
        try:
            self.syllabus_collection = self.client.get_or_create_collection(
                name="syllabus",
                metadata={"description": "Uploaded syllabus documents and course materials"},
            )
        except Exception as e:
            logger.error(f"Failed to get/create syllabus collection: {e}", exc_info=True)
            raise

        # Collection for conversation memory
        try:
            self.memory_collection = self.client.get_or_create_collection(
                name="conversations",
                metadata={"description": "Past conversation history for context retrieval"},
            )
        except Exception as e:
            logger.error(f"Failed to get/create memory collection: {e}", exc_info=True)
            raise
        self._initialized = True
        logger.info("VectorStore initialized successfully")

    # ── Document Operations ────────────────────────────────────

    def add_document(self, text: str, doc_id: str, metadata: dict = None):
        """
        Add a document to the syllabus collection in chunks.

        Args:
            text: Full document text.
            doc_id: Unique identifier for the document.
            metadata: Additional metadata (filename, subject, type).
        """
        chunks = self._chunk_text(text, chunk_size=500, overlap=50)

        if not chunks:
            logger.warning(f"No chunks generated for document: {doc_id}")
            return

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                **(metadata or {}),
                "chunk_index": i,
                "doc_id": doc_id,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]

        # Upsert to handle re-uploads of the same document
        self.syllabus_collection.upsert(
            documents=chunks,
            ids=ids,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(chunks)} chunks from document: {doc_id}")

    def search(self, query: str, top_k: int = 5, filter_metadata: dict = None) -> dict:
        """
        Semantic search across syllabus documents.

        Args:
            query: Natural language search query.
            top_k: Number of results to return.
            filter_metadata: Optional ChromaDB where filter.

        Returns:
            ChromaDB query results with documents, metadatas, distances.
        """
        count = self.syllabus_collection.count()
        if count == 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        kwargs = {
            "query_texts": [query],
            "n_results": min(top_k, count),
        }
        if filter_metadata:
            kwargs["where"] = filter_metadata

        try:
            results = self.syllabus_collection.query(**kwargs)
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_document_count(self) -> int:
        """Return total number of chunks in the syllabus collection."""
        return self.syllabus_collection.count()

    def delete_document(self, doc_id: str):
        """Delete all chunks belonging to a specific document."""
        # Get all chunk IDs for this document
        try:
            results = self.syllabus_collection.get(
                where={"doc_id": doc_id}
            )
            if results["ids"]:
                self.syllabus_collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")

    # ── Conversation Memory ────────────────────────────────────

    def save_conversation(self, user_message: str, agent_response: str, user_id: str = "default"):
        """Save a conversation turn to the memory collection for later retrieval."""
        conversation_text = f"User: {user_message}\nAssistant: {agent_response}"
        timestamp = datetime.now(timezone.utc).isoformat()
        conv_id = f"conv_{user_id}_{timestamp}"

        self.memory_collection.upsert(
            documents=[conversation_text],
            ids=[conv_id],
            metadatas=[{
                "type": "conversation",
                "user_id": user_id,
                "timestamp": timestamp,
            }],
        )

    def search_memory(self, query: str, user_id: str = "default", top_k: int = 3) -> list[str]:
        """
        Search past conversations for relevant context.

        Returns:
            List of relevant past conversation snippets.
        """
        count = self.memory_collection.count()
        if count == 0:
            return []

        try:
            results = self.memory_collection.query(
                query_texts=[query],
                n_results=min(top_k, count),
            )

            # Filter by user_id
            relevant = []
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                if meta.get("user_id") == user_id:
                    relevant.append(doc)

            return relevant

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    # ── Utilities ──────────────────────────────────────────────

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Split text into overlapping chunks at sentence boundaries."""
        import re

        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                if overlap > 0 and current_chunk:
                    current_chunk = current_chunk[-overlap:] + sentence + " "
                else:
                    current_chunk = sentence + " "

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

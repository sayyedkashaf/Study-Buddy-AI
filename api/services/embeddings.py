"""
Embeddings Service — Thin wrapper over ChromaDB's built-in embeddings.

ChromaDB uses all-MiniLM-L6-v2 by default (384-dim vectors).
This module exists as an abstraction layer so you can swap to
OpenAI, Cohere, or any other embedding provider later.
"""

import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding abstraction layer.
    
    Currently uses ChromaDB's built-in embedding function.
    To swap providers, modify this class without touching any agent code.
    """

    def __init__(self, provider: str = "chromadb"):
        self.provider = provider
        logger.info(f"Embedding provider: {provider} (ChromaDB default = all-MiniLM-L6-v2)")

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Note: ChromaDB handles this internally during add/query operations.
        This method is here for standalone embedding needs.
        """
        if self.provider == "chromadb":
            # ChromaDB handles embeddings internally
            # This is a no-op placeholder for the interface
            raise NotImplementedError(
                "ChromaDB embeds text internally during add() and query(). "
                "Use VectorStore.add_document() and VectorStore.search() instead."
            )

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if self.provider == "chromadb":
            raise NotImplementedError(
                "ChromaDB embeds text internally. Use VectorStore methods."
            )

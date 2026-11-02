"""
FastAPI dependency injection - shared resources for route handlers.
"""

from api.services.llm_service import LLMService
from api.services.vector_store import VectorStore
from api.services.cache_service import CacheService
from api.agents.orchestrator import Orchestrator

# ── Singleton instances ────────────────────────────────────────
_llm_service = None
_vector_store = None
_cache_service = None
_orchestrator = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_vector_store() -> VectorStore:
    """Get or create VectorStore singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def get_cache_service() -> CacheService:
    """Get or create CacheService singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def get_orchestrator() -> Orchestrator:
    """Get or create Orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

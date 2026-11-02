"""
Study Buddy AI — FastAPI Backend

Main entry point for the API server.
Run with: uvicorn api.main:app --reload --port 8000
Docs at: http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.models.database import init_db
from api.routes import chat, documents, planner, attendance, subjects

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-25s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    # Startup
    logger.info("🚀 Starting Study Buddy API...")
    from api.core.config import UPLOADS_DIR, CHROMA_DIR
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        init_db()
        logger.info("✅ Database and directories initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # Validate config
    try:
        from api.core.config import validate_config
        validate_config()
        logger.info("✅ Gemini API key configured")
    except ValueError as e:
        logger.warning(f"⚠️  {e}")
    except Exception as e:
        logger.error(f"❌ Config validation failed: {e}")
        raise

    # Load embedding model and vector store once at startup
    try:
        logger.info("🧠 Loading embedding model and vector store...")
        from api.services.vector_store import VectorStore
        _vs = VectorStore()
        # Trigger model load by accessing collection
        _ = _vs.syllabus_collection.count()
        logger.info("✅ Embedding model and vector store loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load embedding model/vector store: {e}")
        raise

    logger.info("✅ Study Buddy API is ready!")
    logger.info("📖 API docs at: http://localhost:8000/docs")

    yield  # App runs here

    # Shutdown
    logger.info("👋 Shutting down Study Buddy API...")


# ── FastAPI App ────────────────────────────────────────────────
app = FastAPI(
    title="Study Buddy AI",
    description=(
        "🎓 An agentic AI system that helps university students manage their studies. "
        "Upload syllabus PDFs, chat with specialized AI agents, generate study plans, "
        "and track attendance."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS Middleware ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Streamlit runs on different port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routes ───────────────────────────────────────────
app.include_router(chat.router, prefix="/chat", tags=["💬 Chat"])
app.include_router(documents.router, prefix="/documents", tags=["📄 Documents"])
app.include_router(planner.router, prefix="/planner", tags=["📅 Study Plans"])
app.include_router(attendance.router, prefix="/attendance", tags=["📊 Attendance"])
app.include_router(subjects.router, prefix="/subjects", tags=["📚 Subjects"])


# ── Health Endpoint ────────────────────────────────────────────
@app.get("/health", tags=["🏠 General"])
def health_check():
    """Health check endpoint for monitoring."""
    cache_backend = "in-memory"
    docs_count = 0

    try:
        from api.services.cache_service import CacheService
        cache = CacheService()
        cache_backend = cache.backend
    except Exception as e:
        logger.warning(f"Health check cache probe warning: {e}")

    try:
        from api.services.vector_store import VectorStore
        vector_store = VectorStore()
        docs_count = vector_store.get_document_count()
    except Exception as e:
        logger.warning(f"Health check vector store probe warning: {e}")

    return {
        "status": "healthy",
        "cache_backend": cache_backend,
        "documents_indexed": docs_count,
    }

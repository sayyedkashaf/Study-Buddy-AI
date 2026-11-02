
"""
Application configuration loaded from environment variables.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "none"

logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"

# Auto-create data directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "gemini-3.5-flash-lite")

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'study_buddy.db'}"
)

# Redis (Optional — in-memory cache used if unavailable)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# ChromaDB
CHROMA_PATH = os.getenv("CHROMA_PATH", str(CHROMA_DIR))
Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)

# App settings
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def validate_config():
    """Validate required configuration on startup."""

    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Please add a valid GEMINI_API_KEY to your .env file. "
            "Get a free API key at https://aistudio.google.com/."
        )

    return True

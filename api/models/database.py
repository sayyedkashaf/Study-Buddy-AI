"""
SQLite database connection and session management via SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from api.core.config import DATABASE_URL

# ── Engine ─────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False,
)

# ── Session Factory ────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base Model ─────────────────────────────────────────────────
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.
    Automatically closes the session after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables in the database."""
    # Import all models so they are registered with Base
    from api.models import user, subject, study_plan, attendance, timetable  # noqa: F401
    Base.metadata.create_all(bind=engine)

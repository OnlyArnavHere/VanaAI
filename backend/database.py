"""
Database connection and session management.
Uses PostgreSQL + PostGIS for spatial queries.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://vanai:vanai_secret@localhost:5432/vanai_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on startup."""
    from models.zone import Zone  # noqa: F401
    from models.analysis import AnalysisResult  # noqa: F401
    Base.metadata.create_all(bind=engine)

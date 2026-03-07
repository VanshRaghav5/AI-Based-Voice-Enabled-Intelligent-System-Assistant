"""Database initialization and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os

# Create Base for model declarations
Base = declarative_base()

# Database file location
DB_DIR = os.path.join(os.path.expanduser("~"), ".omniassist")
DB_PATH = os.path.join(DB_DIR, "assistant.db")

# Ensure directory exists
os.makedirs(DB_DIR, exist_ok=True)

# Create engine (SQLite for simplicity, can be changed to PostgreSQL/MySQL)
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False  # Set to True for SQL query debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from backend.database.models import User, Session
    Base.metadata.create_all(bind=engine)

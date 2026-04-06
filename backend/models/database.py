"""Database initialization and session management."""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os
import time

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
    """Initialize database tables and apply schema migrations."""
    from backend.models.models import User, Session
    Base.metadata.create_all(bind=engine)
    
    # Apply schema migrations for existing databases
    migrate_db_schema()


def migrate_db_schema():
    """Apply schema migrations to handle missing columns in existing tables."""
    try:
        # Get inspector to check table structure
        inspector = inspect(engine)
        
        # Check if users table exists
        if "users" not in inspector.get_table_names():
            return
        
        # Get list of columns in users table
        columns = [column["name"] for column in inspector.get_columns("users")]
        
        # Connect directly to add missing columns
        with engine.begin() as connection:
            # Add is_email_verified if missing
            if "is_email_verified" not in columns:
                try:
                    connection.execute(text(
                        "ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN DEFAULT 0 NOT NULL"
                    ))
                except Exception:
                    pass  # Column might already exist
            
            # Add email_verified_at if missing
            if "email_verified_at" not in columns:
                try:
                    connection.execute(text(
                        "ALTER TABLE users ADD COLUMN email_verified_at DATETIME"
                    ))
                except Exception:
                    pass  # Column might already exist
                    
    except Exception as e:
        # Silent fail - DB might be locked or in use
        pass

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to SQLite local database file for development, switch to Postgres via env in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finguard.db")

# For SQLite, we require 'check_same_thread=False' to support async FastAPI requests
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency to yield database sessions to endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

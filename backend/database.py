from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base
from backend.core.config import settings

# Unified PostgreSQL Database
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import all models to ensure metadata is registered before create_all
import backend.models.job
import backend.models.resume
import backend.models.core

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

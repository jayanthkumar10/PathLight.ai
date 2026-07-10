from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from .base import Base

class MasterResume(Base):
    __tablename__ = 'master_resumes'

    id = Column(String(36), primary_key=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    parsed_text = Column(Text, nullable=True)
    parsed_json = Column(Text, nullable=True)
    hard_skills = Column(Text, nullable=True)
    soft_skills = Column(Text, nullable=True)
    technical_skills = Column(Text, nullable=True)
    action_verbs = Column(Text, nullable=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class TailoringJob(Base):
    __tablename__ = 'tailoring_jobs'

    id = Column(String(36), primary_key=True)
    status = Column(String(50), nullable=False, default='pending')
    selected_model = Column(String(100), nullable=False)
    target_role = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    posted_within = Column(String(50), nullable=True)
    requested_jobs = Column(Integer, default=0)
    min_confidence = Column(Integer, default=55)
    scanned_jobs = Column(Integer, default=0)      # actual jobs returned by Apify
    matched_jobs = Column(Integer, default=0)      # passed YOE filter
    generated_resumes = Column(Integer, default=0) # successfully tailored
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    applications = relationship("Application", back_populates="tailoring_job")
    scraped_jobs = relationship("ScrapedJob", back_populates="tailoring_job")


class ScrapedJob(Base):
    __tablename__ = 'scraped_jobs'

    id = Column(String(36), primary_key=True)
    tailoring_job_id = Column(String(36), ForeignKey('tailoring_jobs.id'), nullable=False)
    apify_id = Column(String(255), nullable=True)
    url = Column(String(512), nullable=True)
    raw_html = Column(Text, nullable=True)
    normalized_json = Column(JSON, nullable=True)
    raw_data = Column(JSON, nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

    tailoring_job = relationship("TailoringJob", back_populates="scraped_jobs")


class JDIntelligenceCache(Base):
    __tablename__ = 'jd_intelligence_cache'

    jd_hash = Column(String(64), primary_key=True)
    extracted_skills = Column(JSON, nullable=False)
    required_yoe = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EvidenceMap(Base):
    __tablename__ = 'evidence_maps'

    id = Column(String(36), primary_key=True)
    resume_hash = Column(String(64), nullable=False)
    jd_hash = Column(String(64), nullable=False)
    evidence_json = Column(JSON, nullable=False)
    rewrite_plan_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Application(Base):
    __tablename__ = 'applications'

    id = Column(String(36), primary_key=True)
    tailoring_job_id = Column(String(36), ForeignKey('tailoring_jobs.id'), nullable=False)
    scraped_job_id = Column(String(36), ForeignKey('scraped_jobs.id'), nullable=True)
    
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    apply_link = Column(String(512), nullable=True)
    linkedin_url = Column(String(512), nullable=True)
    job_description = Column(Text, nullable=True)
    
    prompt_used = Column(Text, nullable=True)
    generated_resume_path = Column(String(512), nullable=True)
    generated_html = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    fit_score = Column(Float, nullable=True)
    match_confidence = Column(Integer, nullable=True)
    generation_time = Column(Float, nullable=True)
    injected_keywords = Column(Text, nullable=True)
    missing_keywords = Column(Text, nullable=True)
    application_status = Column(String(50), default='draft')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tailoring_job = relationship("TailoringJob", back_populates="applications")

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# Application Schemas
class ApplicationBase(BaseModel):
    job_title: str
    company: str
    location: Optional[str] = None
    apply_link: Optional[str] = None
    linkedin_url: Optional[str] = None
    job_description: Optional[str] = None
    scraped_job_id: Optional[str] = None
    prompt_used: Optional[str] = None
    generated_resume_path: Optional[str] = None
    generated_html: Optional[str] = None
    ats_score: Optional[float] = None
    fit_score: Optional[float] = None
    generation_time: Optional[float] = None
    injected_keywords: Optional[str] = None
    missing_keywords: Optional[str] = None
    application_status: Optional[str] = 'draft'

class ApplicationCreate(ApplicationBase):
    tailoring_job_id: str

class ManualApplicationCreate(BaseModel):
    company: str
    job_title: str
    location: Optional[str] = None
    apply_link: Optional[str] = None
    application_status: Optional[str] = 'Applied'

class ApplicationUpdate(BaseModel):
    application_status: Optional[str] = None

class ApplicationResponse(ApplicationBase):
    id: str
    tailoring_job_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# TailoringJob Schemas
class TailoringJobBase(BaseModel):
    selected_model: str
    target_role: str
    location: Optional[str] = None
    posted_within: Optional[str] = None

class TailoringJobCreate(TailoringJobBase):
    requested_jobs: int = 10

class SingleTailorCreate(BaseModel):
    job_url: Optional[str] = None
    job_description: str
    selected_model: str

class ExtensionJobCreate(BaseModel):
    title: str
    company: str
    location: str
    url: str
    descriptionText: str
    employmentType: Optional[str] = "Full-time"

class TailoringJobUpdate(BaseModel):
    status: Optional[str] = None
    requested_jobs: Optional[int] = None
    scanned_jobs: Optional[int] = None
    matched_jobs: Optional[int] = None
    generated_resumes: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TailoringJobResponse(TailoringJobBase):
    id: str
    status: str
    requested_jobs: int
    scanned_jobs: int = 0
    matched_jobs: int
    generated_resumes: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    applications: List[ApplicationResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

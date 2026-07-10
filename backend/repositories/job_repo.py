from typing import List
from sqlalchemy.orm import Session
from backend.models.job import TailoringJob, Application
from backend.schemas.job import (
    TailoringJobCreate, TailoringJobUpdate, 
    ApplicationCreate, ApplicationBase
)
from backend.repositories.base import BaseRepository

class TailoringJobRepository(BaseRepository[TailoringJob, TailoringJobCreate, TailoringJobUpdate]):
    def get_active_jobs(self, db: Session) -> List[TailoringJob]:
        return db.query(self.model).filter(self.model.status.in_(['pending', 'processing'])).all()

class ApplicationRepository(BaseRepository[Application, ApplicationCreate, ApplicationBase]):
    def get_by_job_id(self, db: Session, job_id: str) -> List[Application]:
        return db.query(self.model).filter(self.model.tailoring_job_id == job_id).all()
        
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Application]:
        return db.query(self.model).order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()

tailoring_job_repo = TailoringJobRepository(TailoringJob)
application_repo = ApplicationRepository(Application)

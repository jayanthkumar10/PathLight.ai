from typing import Optional
from sqlalchemy.orm import Session
from backend.models.resume import MasterResume
from backend.schemas.resume import MasterResumeCreate, MasterResumeBase
from backend.repositories.base import BaseRepository

class MasterResumeRepository(BaseRepository[MasterResume, MasterResumeCreate, MasterResumeBase]):
    def get_by_hash(self, db: Session, hash_val: str) -> Optional[MasterResume]:
        return db.query(self.model).filter(self.model.hash == hash_val).first()

master_resume_repo = MasterResumeRepository(MasterResume)

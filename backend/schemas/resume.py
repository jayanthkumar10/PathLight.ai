from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class MasterResumeBase(BaseModel):
    original_filename: str
    storage_path: str
    hash: str
    parsed_text: Optional[str] = None
    parsed_json: Optional[str] = None

class MasterResumeCreate(MasterResumeBase):
    pass

class MasterResumeResponse(MasterResumeBase):
    id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

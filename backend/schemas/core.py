from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    firstName: Optional[str]
    lastName: Optional[str]
    profileImage: Optional[str]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class StepData(BaseModel):
    stepNumber: int
    stepData: Optional[Dict[str, Any]] = None
from datetime import datetime

class LinkedInSearchCreate(BaseModel):
    role: str
    locations: List[str]
    postedWithin: str
    maxJobs: int
    experienceMode: str

class LinkedInSearchResponse(BaseModel):
    id: str
    userId: str
    searchName: Optional[str]
    role: str
    locations: List[str]
    postedWithin: str
    maxJobs: int
    experienceMode: str
    searchStatus: str
    jobsScraped: int
    jobsProcessed: int
    jobsTailored: int
    jobsSkipped: int
    jobsApplied: int
    startedAt: Optional[datetime]
    completedAt: Optional[datetime]
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

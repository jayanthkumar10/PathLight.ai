from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.core import User, Resume
from backend.services.auth_service import get_current_authenticated_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/overview")
def get_overview(current_user: User = Depends(get_current_authenticated_user)):
    return {
        "healthScore": 85,
        "applicationsActive": 0,
        "interviewsUpcoming": 0,
        "recruiterResponses": 0
    }

@router.get("/applications")
def get_applications(current_user: User = Depends(get_current_authenticated_user)):
    return []

@router.get("/interviews")
def get_interviews(current_user: User = Depends(get_current_authenticated_user)):
    return []

@router.get("/recruiters")
def get_recruiters(current_user: User = Depends(get_current_authenticated_user)):
    return []

@router.get("/resumes")
def get_resumes(current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    resumes = db.query(Resume).filter(Resume.userId == current_user.id).order_by(Resume.createdAt.desc()).limit(5).all()
    
    return {
        "versions": [{"id": r.id, "name": r.fileName, "date": r.createdAt.isoformat()} for r in resumes],
        "atsScore": 78
    }

@router.get("/recommendations")
def get_recommendations(current_user: User = Depends(get_current_authenticated_user)):
    return []

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.core import User, MasterProfile
from backend.services.auth_service import get_current_authenticated_user

router = APIRouter(prefix="/api/studio", tags=["studio"])

@router.get("")
def get_master_profile(current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    """Fetches the user's Dynamic Master Profile."""
    profile = db.query(MasterProfile).filter(MasterProfile.userId == current_user.id).first()
    if not profile:
        return {"status": "none"}
    
    return {
        "status": "success",
        "profile": {
            "contactInfo": profile.contactInfo or {},
            "targetTitles": profile.targetTitles or [],
            "workExperience": profile.workExperience or [],
            "projects": profile.projects or [],
            "education": profile.education or [],
            "skills": profile.skills or {},
            "achievements": profile.achievements or []
        }
    }

@router.put("")
def save_master_profile(payload: dict = Body(...), current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    """Creates or updates the user's Dynamic Master Profile."""
    profile = db.query(MasterProfile).filter(MasterProfile.userId == current_user.id).first()
    
    if not profile:
        profile = MasterProfile(userId=current_user.id)
        db.add(profile)
    
    # Update fields from payload
    profile.contactInfo = payload.get("contactInfo", {})
    profile.targetTitles = payload.get("targetTitles", [])
    profile.workExperience = payload.get("workExperience", [])
    profile.projects = payload.get("projects", [])
    profile.education = payload.get("education", [])
    profile.skills = payload.get("skills", {})
    profile.achievements = payload.get("achievements", [])
    
    db.commit()
    
    return {"status": "success", "message": "Master Profile saved."}

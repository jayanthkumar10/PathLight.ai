from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import logging
from backend.database import get_db
from backend.models.core import User, Resume, ResumeVersion
from backend.services.auth_service import get_current_authenticated_user
from backend.services.resume_service import process_and_save_resume

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["resume"])

@router.get("/current")
def get_current_resume(current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    """Returns the active Master Resume."""
    resume = db.query(Resume).filter(
        Resume.userId == current_user.id,
        Resume.status == "ACTIVE"
    ).first()
    
    if not resume:
        return {"status": "none"}
        
    archived_count = db.query(Resume).filter(
        Resume.userId == current_user.id,
        Resume.status == "ARCHIVED"
    ).count()
    
    version = None
    if resume.processingStatus == "COMPLETED":
        version = db.query(ResumeVersion).filter(
            ResumeVersion.resumeId == resume.id,
            ResumeVersion.versionNumber == 1
        ).first()
        
    return {
        "status": "ready",
        "resume": {
            "id": resume.id,
            "fileName": resume.fileName,
            "fileSize": resume.fileSize,
            "createdAt": resume.createdAt.isoformat(),
            "processingStatus": resume.processingStatus,
            "pageCount": resume.pageCount,
            "version1_ready": version is not None,
            "archivedCount": archived_count
        }
    }

@router.post("/upload")
async def upload_resume(
    resume: UploadFile = File(...), 
    source: str = "profile",
    current_user: User = Depends(get_current_authenticated_user), 
    db: Session = Depends(get_db)
):
    """Uploads a new Master Resume (Onboarding or Profile)."""
    return process_and_save_resume(db, current_user.id, resume, source)

@router.put("/replace")
async def replace_resume(
    resume: UploadFile = File(...), 
    current_user: User = Depends(get_current_authenticated_user), 
    db: Session = Depends(get_db)
):
    """Replaces the Master Resume (Archives the old one)."""
    return process_and_save_resume(db, current_user.id, resume, "profile_replace")

@router.get("/download/{resume_id}")
def download_resume(
    resume_id: str, 
    current_user: User = Depends(get_current_authenticated_user), 
    db: Session = Depends(get_db)
):
    """Downloads the original file for a given resume ID."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.userId == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    if not os.path.exists(resume.fileUrl):
        raise HTTPException(status_code=404, detail="Original file not found on disk")
        
    return FileResponse(
        resume.fileUrl, 
        media_type=resume.mimeType or "application/octet-stream",
        filename=resume.fileName
    )

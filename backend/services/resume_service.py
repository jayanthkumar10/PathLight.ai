import os
import uuid
import logging
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from backend.models.core import Resume, ResumeVersion
from .resume_parser.engine import process_resume

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB

def process_and_save_resume(db: Session, user_id: str, file: UploadFile, upload_source: str) -> dict:
    """Handles secure file saving, extraction, and database persistence."""
    # 1. Validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
        
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
        
    # 2. Secure Storage
    os.makedirs("uploads/resumes", exist_ok=True)
    safe_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join("uploads/resumes", safe_filename)
    
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
        
    # 3. Archive old active resumes
    old_resumes = db.query(Resume).filter(
        Resume.userId == user_id, 
        Resume.status == "ACTIVE"
    ).all()
    for old_res in old_resumes:
        old_res.status = "ARCHIVED"
        old_res.processingStatus = "ARCHIVED"
        
    # 4. Processing Pipeline
    try:
        parsed_result = process_resume(file_path, file.content_type or "application/pdf")
    except Exception as e:
        logger.error(f"Failed to parse resume: {e}")
        # Even if parsing fails, we might want to store the failed resume so user knows
        parsed_result = {
            "raw_text": "",
            "structured_data": {},
            "metadata": {
                "checksum": "",
                "parser_version": "error",
                "extraction_time_ms": 0,
                "page_count": 0,
                "word_count": 0,
                "section_count": 0,
                "error": str(e)
            }
        }
        
    meta = parsed_result["metadata"]
    
    # 5. Database Persistence
    db_resume = Resume(
        userId=user_id,
        fileUrl=file_path,
        fileName=file.filename,
        status="ACTIVE" if not meta.get("error") else "ERROR",
        checksum=meta.get("checksum"),
        fileSize=file_size,
        mimeType=file.content_type,
        pageCount=meta.get("page_count"),
        wordCount=meta.get("word_count"),
        uploadSource=upload_source,
        processingStatus="COMPLETED" if not meta.get("error") else "FAILED",
        parserVersion=meta.get("parser_version")
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    
    if not meta.get("error"):
        db_version = ResumeVersion(
            resumeId=db_resume.id,
            versionNumber=1,
            parsedText=parsed_result["raw_text"],
            structuredData=parsed_result["structured_data"],
            metadata_=meta
        )
        db.add(db_version)
        db.commit()
        
    if meta.get("error"):
        raise HTTPException(status_code=422, detail=f"Failed to process file: {meta.get('error')}")

    return {
        "success": True, 
        "resumeId": db_resume.id, 
        "status": db_resume.processingStatus
    }

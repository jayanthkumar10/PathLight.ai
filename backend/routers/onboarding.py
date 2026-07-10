from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode
import httpx
import os
import uuid
import logging
from backend.database import get_db
from backend.models.core import User, Onboarding, Resume, ResumeProcessingJob, GoogleConnection
from backend.schemas.core import StepData
from backend.services.auth_service import get_current_authenticated_user
from backend.services.resume_service import process_and_save_resume

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["onboarding"])

ONBOARDING_TOTAL_STEPS = 8

@router.get("/onboarding/state")
def get_state(current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    onboarding = db.query(Onboarding).filter(Onboarding.userId == current_user.id).first()
    if not onboarding:
        onboarding = Onboarding(userId=current_user.id)
        db.add(onboarding)
        db.commit()
        db.refresh(onboarding)
        
    return {
        "currentStep": onboarding.currentStep,
        "completedSteps": onboarding.completedSteps or [],
        "resumeUploaded": onboarding.resumeUploaded,
        "resumeProcessed": onboarding.resumeProcessed,
        "gmailConnected": onboarding.googleConnected,
        "onboardingCompleted": onboarding.onboardingCompleted
    }

@router.post("/onboarding/step")
def update_step(step: StepData, current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    onboarding = db.query(Onboarding).filter(Onboarding.userId == current_user.id).first()
    if not onboarding:
        onboarding = Onboarding(userId=current_user.id)
        db.add(onboarding)
        db.commit()
        db.refresh(onboarding)

    completed = onboarding.completedSteps or []
    if step.stepNumber not in completed:
        completed.append(step.stepNumber)
        
    onboarding.completedSteps = completed
    onboarding.currentStep = step.stepNumber + 1
    
    if step.stepNumber >= ONBOARDING_TOTAL_STEPS - 1:
        onboarding.currentStep = ONBOARDING_TOTAL_STEPS
        onboarding.onboardingCompleted = True
        
    db.commit()
    return {"success": True, "nextStep": onboarding.currentStep}

@router.post("/onboarding/upload")
async def upload_resume(resume: UploadFile = File(...), current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    result = process_and_save_resume(db, current_user.id, resume, "onboarding")
    
    onboarding = db.query(Onboarding).filter(Onboarding.userId == current_user.id).first()
    if not onboarding:
        onboarding = Onboarding(userId=current_user.id)
        db.add(onboarding)
    
    onboarding.resumeUploaded = True
    onboarding.currentStep = 6
    db.commit()
    
    return {"success": True, "resumeId": result["resumeId"], "jobId": "sync"}

@router.post("/onboarding/google-skip")
def google_skip(current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    onboarding = db.query(Onboarding).filter(Onboarding.userId == current_user.id).first()
    if onboarding:
        onboarding.currentStep = 7
        onboarding.googleConnected = False
        db.commit()
        return {"success": True, "nextStep": onboarding.currentStep}
    raise HTTPException(status_code=404, detail="Onboarding not found")

@router.get("/onboarding/google-connect")
def google_connect(current_user: User = Depends(get_current_authenticated_user)):
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    params = {
        "client_id": client_id,
        "redirect_uri": "http://localhost:8000/api/onboarding/google-callback",
        "access_type": "offline",
        "response_type": "code",
        "prompt": "consent",
        "scope": "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose",
        "state": current_user.id
    }
    qs = urlencode(params)
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{qs}")

@router.get("/onboarding/google-callback")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "http://localhost:8000/api/onboarding/google-callback",
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("https://oauth2.googleapis.com/token", data=data)
            res.raise_for_status()
            tokens = res.json()
            
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token", "")
            expires_in = tokens.get("expires_in", 3600)
            scope = tokens.get("scope", "")
            
            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_res.raise_for_status()
            user_info = user_res.json()
            email = user_info.get("email")
            
            conn = db.query(GoogleConnection).filter(GoogleConnection.userId == state).first()
            if not conn:
                conn = GoogleConnection(userId=state, email=email, accessToken=access_token, refreshToken=refresh_token, scopes=scope)
                db.add(conn)
            else:
                conn.email = email
                conn.accessToken = access_token
                if refresh_token:
                    conn.refreshToken = refresh_token
                conn.scopes = scope
            
            onboarding = db.query(Onboarding).filter(Onboarding.userId == state).first()
            if onboarding:
                onboarding.googleConnected = True
                onboarding.currentStep = 7
                
            db.commit()
            
            return RedirectResponse("/onboarding?step=7")
        except Exception as e:
            logger.error(f"Google Connect Callback Error: {e}")
            return RedirectResponse("/onboarding?step=6&error=google_connect_failed")

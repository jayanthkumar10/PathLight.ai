from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any
import httpx
import os
import logging
import bcrypt

logger = logging.getLogger(__name__)
from backend.database import get_db
from backend.models.core import User, GoogleConnection, Onboarding
from backend.schemas.core import UserCreate, UserLogin, UserResponse, Token
from backend.services.auth_service import get_current_authenticated_user
from backend.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

@router.post("/signup", response_model=UserResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        passwordHash=hashed_password,
        firstName=user_in.firstName,
        lastName=user_in.lastName
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize onboarding state
    onboarding = Onboarding(userId=new_user.id)
    db.add(onboarding)
    db.commit()

    return new_user

@router.post("/signin")
def signin(user_in: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.passwordHash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Set cookie as it might be expected by frontend
    response.set_cookie(key="token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60, samesite='lax')
    
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email}}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logged out"}

@router.get("/session")
def get_session(current_user: User = Depends(get_current_authenticated_user), db: Session = Depends(get_db)):
    onboarding = db.query(Onboarding).filter(Onboarding.userId == current_user.id).first()
    return {
        "user": {
            "id": current_user.id, 
            "email": current_user.email, 
            "firstName": current_user.firstName,
            "onboarding": {
                "currentStep": onboarding.currentStep if onboarding else 1,
                "onboardingCompleted": onboarding.onboardingCompleted if onboarding else False
            }
        }
    }

@router.post("/forgot-password")
def forgot_password():
    return {"message": "Not implemented"}

from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

# Google OAuth endpoints (if frontend relies on /api/auth/google)
@router.get("/google")
def google_auth():
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "558554285741-2jggohpi8esa8rl6g4s3d34apmoqeun7.apps.googleusercontent.com")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    scope = "openid profile email"
    
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent"
    })
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(code: str = None, db: Session = Depends(get_db)):
    print("1. Callback entered SUCCESS")
    if not code:
        return RedirectResponse(url="/signin?error=auth_failed")
        
    print("2. Authorization code received SUCCESS")

    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

    data = {
        "code": code,
        "client_id": google_client_id,
        "client_secret": google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("https://oauth2.googleapis.com/token", data=data)
            res.raise_for_status()
            tokens = res.json()
            access_token = tokens.get("access_token")
            print("3. Token exchange SUCCESS")

            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_res.raise_for_status()
            user_info = user_res.json()
            email = user_info.get("email")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
            print("4. Google userinfo SUCCESS")

            print("5. Database session created SUCCESS")
            user = db.query(User).filter(User.email == email).first()
            print("6. User lookup SUCCESS")
            
            if not user:
                hashed_password = get_password_hash("google_oauth_dummy_pass")
                user = User(
                    email=email,
                    passwordHash=hashed_password,
                    firstName=first_name,
                    lastName=last_name
                )
                db.add(user)
                db.flush() # Populate user.id
                onboarding = Onboarding(userId=user.id, currentStep=1, onboardingCompleted=False)
                db.add(onboarding)
                db.commit()
                db.refresh(user)
                db.refresh(onboarding)
                print("7. User creation/update SUCCESS")
                print("8. Database commit SUCCESS")
                print("9. Refresh SUCCESS")
            else:
                onboarding = db.query(Onboarding).filter(Onboarding.userId == user.id).first()
                if not onboarding:
                    onboarding = Onboarding(userId=user.id, currentStep=1, onboardingCompleted=False)
                    db.add(onboarding)
                    db.commit()
                    db.refresh(onboarding)

            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            jwt_token = create_access_token(
                data={"sub": user.id}, expires_delta=access_token_expires
            )
            print("10. JWT creation SUCCESS")

            if onboarding.onboardingCompleted:
                response = RedirectResponse(url="/dashboard")
            else:
                response = RedirectResponse(url=f"/onboarding?step={onboarding.currentStep}")
                
            response.set_cookie(key="token", value=jwt_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60, samesite='lax')
            print("11. Cookie creation SUCCESS")
            
            print("12. Redirect SUCCESS")
            return response

        except Exception as e:
            logger.exception("Google OAuth callback failed")
            raise

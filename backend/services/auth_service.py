from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os

from backend.database import get_db
from backend.models.core import User

# Importing SECRET_KEY and ALGORITHM from security to avoid duplication
from backend.core.security import SECRET_KEY, ALGORITHM

class AuthService:
    @staticmethod
    def get_token_from_cookie(request: Request) -> str:
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        return token

    @staticmethod
    def validate_jwt(token: str) -> str:
        """Validates JWT and returns user_id, raises HTTPException if invalid"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            return user_id
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    @staticmethod
    def load_user(user_id: str, db: Session) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

def get_current_authenticated_user(request: Request, db: Session = Depends(get_db)):
    """
    Canonical authentication dependency. 
    Reads the HTTPOnly cookie, validates JWT, and returns the User.
    Raises 401 Unauthorized if any step fails.
    """
    token = AuthService.get_token_from_cookie(request)
    user_id = AuthService.validate_jwt(token)
    user = AuthService.load_user(user_id, db)
    return user

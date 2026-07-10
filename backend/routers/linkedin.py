from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.services.auth_service import get_current_authenticated_user
from backend.models.core import User
from backend.schemas.core import LinkedInSearchCreate, LinkedInSearchResponse
from backend.services.linkedin_service import LinkedInService

router = APIRouter(prefix="/api/linkedin", tags=["linkedin"])

@router.post("/search", response_model=LinkedInSearchResponse)
def create_linkedin_search(
    search_data: LinkedInSearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # Validation
    if not search_data.role or not search_data.role.strip():
        raise HTTPException(status_code=400, detail="Target Role is required")
    if not search_data.locations or len(search_data.locations) == 0:
        raise HTTPException(status_code=400, detail="At least one location is required")
    if search_data.maxJobs <= 0 or search_data.maxJobs > 100:
        raise HTTPException(status_code=400, detail="Maximum jobs must be between 1 and 100")
        
    return LinkedInService.create_search(db, current_user.id, search_data)

@router.get("/search", response_model=List[LinkedInSearchResponse])
def get_linkedin_searches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return LinkedInService.get_user_searches(db, current_user.id)

@router.get("/search/{search_id}", response_model=LinkedInSearchResponse)
def get_linkedin_search(
    search_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    search = LinkedInService.get_search_by_id(db, search_id, current_user.id)
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    return search

@router.delete("/search/{search_id}")
def delete_linkedin_search(
    search_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    success = LinkedInService.delete_search(db, search_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Search not found")
    return {"success": True}

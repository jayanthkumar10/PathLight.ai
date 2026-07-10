from sqlalchemy.orm import Session
from backend.models.core import LinkedInSearch
from backend.schemas.core import LinkedInSearchCreate

class LinkedInService:
    @staticmethod
    def create_search(db: Session, user_id: str, search_data: LinkedInSearchCreate) -> LinkedInSearch:
        search_name = f"{search_data.role} ({len(search_data.locations)} locations)"
        
        db_search = LinkedInSearch(
            userId=user_id,
            searchName=search_name,
            role=search_data.role,
            locations=search_data.locations,
            postedWithin=search_data.postedWithin,
            maxJobs=search_data.maxJobs,
            experienceMode=search_data.experienceMode,
            searchStatus="PENDING"
        )
        db.add(db_search)
        db.commit()
        db.refresh(db_search)
        return db_search

    @staticmethod
    def get_user_searches(db: Session, user_id: str):
        return db.query(LinkedInSearch).filter(LinkedInSearch.userId == user_id).order_by(LinkedInSearch.createdAt.desc()).all()

    @staticmethod
    def get_search_by_id(db: Session, search_id: str, user_id: str):
        return db.query(LinkedInSearch).filter(LinkedInSearch.id == search_id, LinkedInSearch.userId == user_id).first()

    @staticmethod
    def delete_search(db: Session, search_id: str, user_id: str) -> bool:
        search = db.query(LinkedInSearch).filter(LinkedInSearch.id == search_id, LinkedInSearch.userId == user_id).first()
        if search:
            db.delete(search)
            db.commit()
            return True
        return False

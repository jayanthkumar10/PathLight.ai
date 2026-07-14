import json
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.resume import MasterResume

db = SessionLocal()

print("Seeding Master Resume...")

# Create a mock master resume
resume = MasterResume(
    id="test_resume_123",
    original_filename="my_resume.pdf",
    storage_path="/path/to/resume.pdf",
    hash="1234567890abcdef",
    parsed_text="John Doe\nPython Developer\nI am a great python developer with 5 years of experience in Django and AWS.",
    parsed_json=json.dumps({
        "candidate_name": "John Doe",
        "contact_info": "john@doe.com",
        "education": "BS Computer Science",
        "companies": [
            {"name": "Tech Corp", "title": "Backend Engineer", "bullets": ["Built API with Python", "Deployed on AWS"]}
        ]
    }),
    hard_skills="Python, Django, AWS, SQL",
    soft_skills="Communication, Leadership",
    technical_skills="Git, Docker",
    action_verbs="Built, Deployed, Developed"
)

# Insert into db
db.add(resume)
try:
    db.commit()
    print("Master Resume inserted.")
except Exception as e:
    print(f"Already exists or error: {e}")
    db.rollback()

db.close()

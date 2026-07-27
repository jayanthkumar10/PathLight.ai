import sys, os
sys.path.append('c:\\pathlight.ai')
from backend.database import SessionLocal
from backend.models.job import Application, ScrapedJob

db = SessionLocal()
apps = db.query(Application).order_by(Application.created_at.desc()).limit(4).all()
for a in apps:
    print(f'--- App ID: {a.id} ---')
    print(f'Title: {a.job_title}')
    print(f'Company: {a.company}')
    print(f'Status: {a.application_status}')
    scraped = db.query(ScrapedJob).filter(ScrapedJob.id == a.scraped_job_id).first()
    if scraped:
        raw = scraped.raw_data
        print(f'Raw Title: {raw.get("title")}')
        print(f'Raw Company: {raw.get("company")}')
        desc = raw.get("descriptionText", "")
        print(f'Raw Desc length: {len(desc)}')
    else:
        print('No scraped job found')

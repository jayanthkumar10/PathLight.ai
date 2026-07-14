import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "pathlight_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def process_resume_task(tailoring_job_id: str, raw_job_data: dict):
    from backend.database import SessionLocal
    from backend.models.job import TailoringJob
    from backend.models.resume import MasterResume
    from backend.services.engine.resume_context import get_resume_context
    from backend.services.engine.resume_generator import ResumeGenerator
    from backend.services.pipeline import process_single_job
    import asyncio
    
    db = SessionLocal()
    try:
        # Load necessary DB models
        tailoring_job = db.query(TailoringJob).filter(TailoringJob.id == tailoring_job_id).first()
        master_resume = db.query(MasterResume).order_by(MasterResume.created_at.desc()).first()
        resume_context = get_resume_context(db, master_resume)
        resume_generator = ResumeGenerator()

        if not tailoring_job or not master_resume:
            return {"status": "failed", "reason": "Missing DB records"}

        # Run the async pipeline single job function inside this synchronous celery worker thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(
            process_single_job(db, tailoring_job, raw_job_data, master_resume, resume_context, resume_generator)
        )
        
        if success:
            db.query(TailoringJob).filter(TailoringJob.id == tailoring_job_id).update(
                {"generated_resumes": TailoringJob.generated_resumes + 1},
                synchronize_session=False
            )
            db.commit()
            
        return {"status": "success" if success else "failed"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

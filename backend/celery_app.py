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
def process_resume_task(job_id: str, resume_id: str):
    import time
    time.sleep(2)  # Simulate processing
    return {"status": "success", "job_id": job_id, "resume_id": resume_id}

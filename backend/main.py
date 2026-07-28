"""
Pathlight AI Engine — Unified FastAPI Backend
Entry point for all Pathlight APIs (Auth, Tailoring, Dashboard, Resume).
"""
import logging
import os
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.schemas.job import TailoringJobCreate, TailoringJobResponse, ApplicationResponse, SingleTailorCreate, ManualApplicationCreate, ExtensionJobCreate
from backend.repositories.job_repo import tailoring_job_repo, application_repo
from backend.services.pipeline import run_tailoring_pipeline, run_single_tailoring_pipeline
from backend.models.resume import MasterResume
from backend.models.core import MasterProfile

# Unified Routers
from backend.routers import auth, dashboard, onboarding, linkedin, resume, studio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pathlight Unified API",
    description="Full ATS-optimized resume tailoring platform",
    version="2.0.0"
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include Unified Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(onboarding.router)
app.include_router(linkedin.router)
app.include_router(resume.router)
app.include_router(studio.router)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health_check():
    """Readiness probe."""
    from backend.core.config import settings
    return {
        "status": "ok",
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "apify_configured": bool(settings.APIFY_API_TOKEN),
        "openrouter_configured": bool(settings.OPEN_ROUTER_API_KEY),
    }


# ---------------------------------------------------------------------------
# Tailoring Jobs (ATS Engine)
# ---------------------------------------------------------------------------
@app.post("/api/tailor", response_model=TailoringJobResponse)
def start_tailoring(
    job_request: TailoringJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new tailoring job. Called by the 'Start AI Tailoring' button."""
    logger.info(f"New tailoring request | role={job_request.target_role} | model={job_request.selected_model}")
    job = tailoring_job_repo.create(db, obj_in=job_request)
    background_tasks.add_task(run_tailoring_pipeline, job.id)
    return job

@app.post("/api/tailor/single", response_model=TailoringJobResponse)
def start_single_tailoring(
    job_request: SingleTailorCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a single tailoring job with raw JD text."""
    logger.info(f"New single tailoring request | model={job_request.selected_model}")
    tj_create = TailoringJobCreate(
        target_role="Single Job Tailoring",
        selected_model=job_request.selected_model,
        location="Remote",
        requested_jobs=1
    )
    job = tailoring_job_repo.create(db, obj_in=tj_create)
    background_tasks.add_task(run_single_tailoring_pipeline, job.id, job_request.job_description, job_request.job_url)
    return job

@app.post("/api/extension/tailor", response_model=TailoringJobResponse)
def extension_tailor_job(
    job_request: ExtensionJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a single tailoring job from the Chrome extension."""
    logger.info(f"New extension tailoring request | company={job_request.company}")
    
    # We create a dummy TailoringJob to track this single job execution in the UI
    tj_create = TailoringJobCreate(
        target_role=job_request.title,
        selected_model="mistral-small-latest", # Defaulting to valid mistral model
        location=job_request.location,
        requested_jobs=1
    )
    job = tailoring_job_repo.create(db, obj_in=tj_create)
    
    # Run the single pipeline, passing the extension scraped text
    background_tasks.add_task(run_single_tailoring_pipeline, job.id, job_request.descriptionText, job_request.url, job_request.title, job_request.company, job_request.location)
    return job


@app.get("/api/tailor/{job_id}", response_model=TailoringJobResponse)
def get_tailoring_status(job_id: str, db: Session = Depends(get_db)):
    """Poll tailoring job status."""
    job = tailoring_job_repo.get(db, id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ---------------------------------------------------------------------------
# Applications (ATS Engine)
# ---------------------------------------------------------------------------
@app.post("/api/applications/manual", response_model=ApplicationResponse)
def add_manual_application(app_in: ManualApplicationCreate, db: Session = Depends(get_db)):
    """Manually add an application. Binds to a dummy tailoring job."""
    from backend.models.job import TailoringJob, Application
    from backend.schemas.job import TailoringJobCreate
    import uuid
    
    dummy_job_id = "manual_entry_job_001"
    job = db.query(TailoringJob).filter(TailoringJob.id == dummy_job_id).first()
    if not job:
        job = TailoringJob(
            id=dummy_job_id,
            status="completed",
            selected_model="manual",
            target_role="Manual Entries",
            location="Various",
            requested_jobs=0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
    new_app = Application(
        id=str(uuid.uuid4()),
        tailoring_job_id=dummy_job_id,
        job_title=app_in.job_title,
        company=app_in.company,
        location=app_in.location,
        apply_link=app_in.apply_link,
        application_status=app_in.application_status or 'Applied'
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app

@app.get("/api/applications", response_model=list[ApplicationResponse])
def get_applications(db: Session = Depends(get_db)):
    """Fetch all generated applications."""
    return application_repo.get_all(db, limit=200)


@app.patch("/api/applications/{app_id}/status")
def update_application_status(app_id: str, body: dict, db: Session = Depends(get_db)):
    """Update application status manually."""
    app_obj = application_repo.get(db, id=app_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status field required")
    app_obj.application_status = new_status
    db.commit()
    db.refresh(app_obj)
    return {"id": app_obj.id, "status": app_obj.application_status}


@app.get("/api/applications/{app_id}/download")
def download_resume_html(app_id: str, db: Session = Depends(get_db)):
    """Preview the tailored HTML resume (inline in browser)."""
    app_obj = application_repo.get(db, id=app_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    if not app_obj.generated_html:
        raise HTTPException(status_code=404, detail="No tailored resume found")

    company_clean = "".join(x for x in (app_obj.company or "resume") if x.isalnum() or x == "_")
    role_clean    = "".join(x for x in (app_obj.job_title or "role") if x.isalnum() or x == "_")

    return Response(
        content=app_obj.generated_html,
        media_type="text/html",
        headers={
            "Content-Disposition": f"inline; filename=resume_{company_clean}_{role_clean}.html",
            "X-ATS-Score": str(app_obj.ats_score or 0),
        }
    )


@app.get("/api/applications/{app_id}/pdf")
def download_resume_pdf(app_id: str, db: Session = Depends(get_db)):
    """Serve the ATS-readable PDF for a specific application."""
    app_obj = application_repo.get(db, id=app_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    if not app_obj.generated_resume_path or not os.path.exists(app_obj.generated_resume_path):
        raise HTTPException(status_code=404, detail="No tailored resume PDF found on disk")

    filename = os.path.basename(app_obj.generated_resume_path)

    return FileResponse(
        path=app_obj.generated_resume_path,
        media_type="application/pdf",
        filename=filename
    )


@app.get("/api/applications/{app_id}/compare")
def compare_resume(
    app_id: str, 
    db: Session = Depends(get_db)
):
    """Fetch generated HTML and original parsed text for diffing."""
    app_obj = application_repo.get(db, id=app_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    if not app_obj.generated_html:
        raise HTTPException(status_code=404, detail="No tailored HTML found")

    # Compare current dynamic MasterProfile
    from backend.models.core import MasterProfile
    master_profile = db.query(MasterProfile).first()
    if master_profile:
        # Construct plain text for the diff comparison
        original_text = f"Contact Info:\n{master_profile.contactInfo}\n\n"
        original_text += f"Target Titles:\n{master_profile.targetTitles}\n\n"
        original_text += f"Work Experience:\n{master_profile.workExperience}\n\n"
        original_text += f"Projects:\n{master_profile.projects}\n\n"
        original_text += f"Education:\n{master_profile.education}\n\n"
        original_text += f"Skills:\n{master_profile.skills}\n\n"
        original_text += f"Achievements:\n{master_profile.achievements}"
        
        return {
            "original_text": original_text,
            "generated_html": app_obj.generated_html
        }
    
    # Fallback to legacy MasterResume
    master = db.query(MasterResume).filter(MasterResume.user_id == app_obj.userId).order_by(MasterResume.created_at.desc()).first()
    
    if not master or not master.parsed_text:
        raise HTTPException(status_code=404, detail="No active master resume found to compare against")

    return {
        "original_text": master.parsed_text,
        "generated_html": app_obj.generated_html
    }


@app.delete("/api/applications/{app_id}")
def delete_application(app_id: str, db: Session = Depends(get_db)):
    """Delete an application and its associated PDF."""
    app_obj = application_repo.get(db, id=app_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if app_obj.generated_resume_path and os.path.exists(app_obj.generated_resume_path):
        try:
            os.remove(app_obj.generated_resume_path)
        except Exception as e:
            logger.warning(f"Failed to delete PDF: {e}")
            
    application_repo.delete(db, id=app_id)
    return {"status": "success", "message": "Deleted"}

# ---------------------------------------------------------------------------
# Serve Frontend Static Files
# ---------------------------------------------------------------------------
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/onboarding")
def read_onboarding():
    return FileResponse(os.path.join(frontend_dir, "signin.html"))

@app.get("/{page}.html")
def read_page_html(page: str):
    file_path = os.path.join(frontend_dir, f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Page not found")

@app.get("/css/{file}.css")
def read_css_new(file: str):
    file_path = os.path.join(frontend_dir, "css", f"{file}.css")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/{file}.css")
def read_css_fallback(file: str):
    file_path = os.path.join(frontend_dir, "css", f"{file}.css")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/js/{file}.js")
def read_js_new(file: str):
    file_path = os.path.join(frontend_dir, "js", f"{file}.js")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/{file}.js")
def read_js_fallback(file: str):
    file_path = os.path.join(frontend_dir, "js", f"{file}.js")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/assets/{file}.png")
def read_png_new(file: str):
    file_path = os.path.join(frontend_dir, "assets", f"{file}.png")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/{file}.png")
def read_png_fallback(file: str):
    file_path = os.path.join(frontend_dir, "assets", f"{file}.png")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/{page}")
def read_page(page: str):
    if page == "api":
        raise HTTPException(status_code=404, detail="Not Found")
    file_path = os.path.join(frontend_dir, f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Page not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

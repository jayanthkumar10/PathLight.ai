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
from backend.schemas.job import TailoringJobCreate, TailoringJobResponse, ApplicationResponse, SingleTailorCreate
from backend.repositories.job_repo import tailoring_job_repo, application_repo
from backend.services.pipeline import run_tailoring_pipeline, run_single_tailoring_pipeline

# Unified Routers
from backend.routers import auth, dashboard, onboarding, linkedin, resume

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

@app.get("/{file}.css")
def read_css(file: str):
    file_path = os.path.join(frontend_dir, f"{file}.css")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")
    
@app.get("/{file}.js")
def read_js(file: str):
    file_path = os.path.join(frontend_dir, f"{file}.js")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/{file}.png")
def read_png(file: str):
    file_path = os.path.join(frontend_dir, f"{file}.png")
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

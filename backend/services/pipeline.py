"""
Pathlight AI Engine — Main Processing Pipeline (LangGraph Version)
"""
import logging
import uuid
import time
import asyncio
import hashlib
from datetime import datetime, timezone
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END

from backend.database import SessionLocal
from backend.repositories.job_repo import tailoring_job_repo
from backend.models.resume import MasterResume
from backend.models.job import ScrapedJob, JDIntelligenceCache, EvidenceMap as DBEvidenceMap, Application, TailoringJob
from backend.schemas.job import TailoringJobUpdate

from backend.services.scraper.apify_client import ApifyClient
from backend.services.engine.job_normalizer import normalize_apify_job
from backend.services.engine.yoe_filter import passes_yoe_filter
from backend.services.engine.jd_intelligence import extract_jd_intelligence, extract_jd_metadata
from backend.services.engine.resume_context import get_resume_context
from backend.services.engine.evidence_mapper import map_evidence
from backend.services.engine.resume_generator import ResumeGenerator
from backend.services.engine.ats_evaluator import evaluate_ats_score
from backend.services.engine.pdf_generator_and_validator import generate_and_validate_pdf

logger = logging.getLogger(__name__)

def _status(db, job, status: str, extra: dict = None):
    update_data = {"status": status}
    if extra:
        update_data.update(extra)
    tailoring_job_repo.update(db, db_obj=job, obj_in=TailoringJobUpdate(**update_data))

# ----------------- LANGGRAPH STATE -----------------
class AgentState(TypedDict):
    job_id: str
    app_id: str
    master_profile: dict
    resume_context: dict
    raw_job_data: dict
    norm_job: dict
    jd_intel: dict
    evidence_dict: dict
    model_pref: str
    bypass_yoe: bool
    
    summary_data: dict
    exp_data: dict
    proj_data: dict
    
    assembled_html: str
    ats_score: float
    ats_feedback: str
    retry_count: int
    
    pdf_path: str
    final_status: str

# ----------------- LANGGRAPH NODES -----------------

def normalize_and_init(state: AgentState):
    db = SessionLocal()
    try:
        norm_job = normalize_apify_job(state["raw_job_data"])
        
        apify_id = state["raw_job_data"].get("id")
        if apify_id and not str(apify_id).startswith("single_"):
            existing = db.query(ScrapedJob).filter(ScrapedJob.apify_id == apify_id).first()
            if existing:
                return {"final_status": "rejected", "norm_job": norm_job.model_dump()}

        scraped = ScrapedJob(
            id=str(uuid.uuid4()),
            tailoring_job_id=state["job_id"],
            apify_id=state["raw_job_data"].get("id"),
            url=norm_job.apply_url,
            raw_html=state["raw_job_data"].get("descriptionText", ""),
            normalized_json=norm_job.model_dump(),
            raw_data=state["raw_job_data"]
        )
        db.add(scraped)
        db.flush()
        
        app = Application(
            id=str(uuid.uuid4()),
            tailoring_job_id=state["job_id"],
            scraped_job_id=scraped.id,
            job_title=norm_job.title,
            company=norm_job.company,
            location=norm_job.location,
            apply_link=norm_job.apply_url,
            application_status="processing"
        )
        db.add(app)
        db.commit()
        
        if not state["bypass_yoe"]:
            candidate_yoe = state["resume_context"].get("years_of_experience", 2)
            passed, reason = passes_yoe_filter(norm_job, candidate_yoe)
            if not passed:
                app.application_status = "Rejected"
                app.missing_keywords = f"Rejected by YOE filter: {reason}"
                db.commit()
                return {"final_status": "rejected", "app_id": app.id, "norm_job": norm_job.model_dump()}
                
        return {"app_id": app.id, "norm_job": norm_job.model_dump(), "final_status": "processing"}
    finally:
        db.close()

def extract_jd(state: AgentState):
    if state.get("final_status") == "rejected":
        return {}
        
    db = SessionLocal()
    try:
        norm_job = state["norm_job"]
        jd_hash = hashlib.sha256((norm_job["title"] + norm_job["description_text"]).encode()).hexdigest()
        jd_cache = db.query(JDIntelligenceCache).filter(JDIntelligenceCache.jd_hash == jd_hash).first()
        
        if jd_cache:
            jd_intel = jd_cache.extracted_skills
        else:
            extraction_obj = extract_jd_intelligence(norm_job["description_text"])
            jd_intel = extraction_obj.model_dump()
            jd_cache = JDIntelligenceCache(
                jd_hash=jd_hash,
                extracted_skills=jd_intel,
                required_yoe=norm_job["yoe_required"]
            )
            db.add(jd_cache)
            db.commit()
            
        return {"jd_intel": jd_intel}
    finally:
        db.close()

def map_evidence_node(state: AgentState):
    if state.get("final_status") == "rejected":
        return {}
        
    db = SessionLocal()
    try:
        norm_job = state["norm_job"]
        jd_intel = state["jd_intel"]
        resume_hash = state["resume_context"]["hash"]
        jd_hash = hashlib.sha256((norm_job["title"] + norm_job["description_text"]).encode()).hexdigest()
        
        evidence_cache = db.query(DBEvidenceMap).filter(
            DBEvidenceMap.jd_hash == jd_hash,
            DBEvidenceMap.resume_hash == resume_hash
        ).first()
        
        if evidence_cache:
            evidence_dict = evidence_cache.evidence_json
        else:
            from backend.services.engine.jd_intelligence import JDExtraction
            extraction_model = JDExtraction(**jd_intel)
            gap_obj = map_evidence(extraction_model, state["resume_context"])
            evidence_dict = gap_obj.model_dump()
            
            e_map = DBEvidenceMap(
                id=str(uuid.uuid4()),
                resume_hash=resume_hash,
                jd_hash=jd_hash,
                evidence_json=evidence_dict,
                rewrite_plan_json={}
            )
            db.add(e_map)
            db.commit()
            
        return {"evidence_dict": evidence_dict}
    finally:
        db.close()

def generate_summary(state: AgentState):
    if state.get("final_status") == "rejected":
        return {}
    rg = ResumeGenerator()
    from backend.services.engine.jd_intelligence import JDExtraction
    from backend.services.engine.evidence_mapper import GapAnalysis
    
    mock_job = type('MockJob', (), state["norm_job"])()
    jd_ext = JDExtraction(**state["jd_intel"])
    gap = GapAnalysis(**state["evidence_dict"])
    
    res, _ = rg.generate_summary(state["resume_context"]["parsed_text"], state["resume_context"], mock_job, jd_ext, gap, state["model_pref"], state.get("ats_feedback", ""))
    return {"summary_data": res}

def generate_experience(state: AgentState):
    if state.get("final_status") == "rejected":
        return {}
    rg = ResumeGenerator()
    from backend.services.engine.jd_intelligence import JDExtraction
    from backend.services.engine.evidence_mapper import GapAnalysis
    
    mock_job = type('MockJob', (), state["norm_job"])()
    jd_ext = JDExtraction(**state["jd_intel"])
    gap = GapAnalysis(**state["evidence_dict"])
    
    res, _ = rg.generate_experience(state["master_profile"].get("workExperience", []), mock_job, jd_ext, gap, state["model_pref"], state.get("ats_feedback", ""))
    return {"exp_data": res}

def generate_projects(state: AgentState):
    if state.get("final_status") == "rejected":
        return {}
    rg = ResumeGenerator()
    from backend.services.engine.jd_intelligence import JDExtraction
    from backend.services.engine.evidence_mapper import GapAnalysis
    
    mock_job = type('MockJob', (), state["norm_job"])()
    jd_ext = JDExtraction(**state["jd_intel"])
    gap = GapAnalysis(**state["evidence_dict"])
    
    res, _ = rg.generate_projects(state["master_profile"].get("projects", []), mock_job, jd_ext, gap, state["model_pref"], state.get("ats_feedback", ""))
    return {"proj_data": res}

def assemble_html(state: AgentState):
    if state.get("final_status") == "rejected":
        return {}
    rg = ResumeGenerator()
    
    class MP:
        def __init__(self, d):
            self.targetTitles = d.get("targetTitles", [])
            self.contactInfo = d.get("contactInfo", {})
            self.skills = d.get("skills", {})
            self.workExperience = d.get("workExperience", [])
            self.projects = d.get("projects", [])
            self.education = d.get("education", [])
            self.achievements = d.get("achievements", [])
            
    mp = MP(state["master_profile"])
    mock_job = type('MockJob', (), state["norm_job"])()
    html = rg.assemble_html(mp, mock_job, state.get("summary_data",{}), state.get("exp_data",{}), state.get("proj_data",{}))
    return {"assembled_html": html}

def evaluate_ats(state: AgentState):
    if state.get("final_status") == "rejected":
        return {}
    from backend.services.engine.evidence_mapper import GapAnalysis
    gap = GapAnalysis(**state["evidence_dict"])
    missing_for_eval = gap.missing_hard_skills + gap.missing_technical_skills
    eval_result = evaluate_ats_score(state["assembled_html"], missing_for_eval)
    return {
        "ats_score": eval_result.overall_ats_score,
        "ats_feedback": eval_result.feedback,
        "retry_count": state.get("retry_count", 0) + 1
    }

def route_ats(state: AgentState):
    if state.get("final_status") == "rejected":
        return "generate_pdf"
    if state["ats_score"] >= 85 or state["retry_count"] >= 2:
        return "generate_pdf"
    return ["regenerate_summary", "regenerate_experience", "regenerate_projects"]

def generate_pdf_node(state: AgentState):
    if state.get("final_status") == "rejected":
        return {}
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == state["app_id"]).first()
        if not app:
            return {}
            
        pdf_path = generate_and_validate_pdf(state["assembled_html"], app.job_title, app.company)
        
        app.generated_html = state["assembled_html"]
        app.generated_resume_path = pdf_path
        app.ats_score = state["ats_score"]
        app.fit_score = state["ats_score"]
        app.missing_keywords = state["ats_feedback"]
        app.application_status = "completed"
        db.commit()
        return {"final_status": "completed", "pdf_path": pdf_path}
    finally:
        db.close()

# Compile Graph
graph = StateGraph(AgentState)

graph.add_node("normalize_and_init", normalize_and_init)
graph.add_node("extract_jd", extract_jd)
graph.add_node("map_evidence", map_evidence_node)
graph.add_node("generate_summary", generate_summary)
graph.add_node("generate_experience", generate_experience)
graph.add_node("generate_projects", generate_projects)
graph.add_node("assemble_html", assemble_html)
graph.add_node("evaluate_ats", evaluate_ats)
graph.add_node("generate_pdf", generate_pdf_node)

graph.add_edge(START, "normalize_and_init")
graph.add_edge("normalize_and_init", "extract_jd")
graph.add_edge("extract_jd", "map_evidence")
graph.add_edge("map_evidence", "generate_summary")
graph.add_edge("map_evidence", "generate_experience")
graph.add_edge("map_evidence", "generate_projects")
graph.add_edge("generate_summary", "assemble_html")
graph.add_edge("generate_experience", "assemble_html")
graph.add_edge("generate_projects", "assemble_html")
graph.add_edge("assemble_html", "evaluate_ats")

graph.add_conditional_edges(
    "evaluate_ats",
    route_ats,
    {
        "generate_pdf": "generate_pdf",
        "regenerate_summary": "generate_summary",
        "regenerate_experience": "generate_experience",
        "regenerate_projects": "generate_projects"
    }
)
graph.add_edge("generate_pdf", END)

compiled_graph = graph.compile()

async def run_single_tailoring_pipeline(job_id: str, jd_text: str, job_url: str, company: str = None, location: str = None):
    logger.info(f"{'='*60}\nSingle Pipeline START — Job ID: {job_id}\n{'='*60}")

    db = SessionLocal()
    try:
        job = tailoring_job_repo.get(db, job_id)
        if not job:
            return

        _status(db, job, "Preparing", {"started_at": datetime.now(timezone.utc)})

        master_resume = db.query(MasterResume).order_by(MasterResume.created_at.desc()).first()
        if not master_resume:
            logger.error("No master resume found. Cannot tailor.")
            _status(db, job, "Failed", {"completed_at": datetime.now(timezone.utc)})
            return
            
        resume_context = get_resume_context(db, master_resume)
        resume_context["hash"] = master_resume.hash
        resume_context["parsed_text"] = master_resume.parsed_text

        metadata = extract_jd_metadata(jd_text)
        job.scanned_jobs = 1
        db.commit()

        raw_job_data = {
            "title": metadata.job_title,
            "company": company if company else metadata.company,
            "location": location if location else metadata.location,
            "employmentType": metadata.employment_type,
            "salaryRange": metadata.salary_range,
            "url": job_url or "",
            "descriptionText": jd_text,
            "id": f"single_{job_id}"
        }

        _status(db, job, "Tailoring")
        
        from backend.models.core import MasterProfile
        mp = db.query(MasterProfile).first()
        mp_dict = mp.model_dump() if hasattr(mp, "model_dump") else mp.__dict__ if mp else {}
        
        if 'work_experience' in mp_dict and not 'workExperience' in mp_dict:
            mp_dict['workExperience'] = mp_dict['work_experience']
        if 'contact_info' in mp_dict and not 'contactInfo' in mp_dict:
            mp_dict['contactInfo'] = mp_dict['contact_info']
        if 'target_titles' in mp_dict and not 'targetTitles' in mp_dict:
            mp_dict['targetTitles'] = mp_dict['target_titles']
        
        initial_state = {
            "job_id": job_id,
            "master_profile": mp_dict,
            "resume_context": resume_context,
            "raw_job_data": raw_job_data,
            "model_pref": job.selected_model,
            "bypass_yoe": True,
            "retry_count": 0
        }
        
        result = compiled_graph.invoke(initial_state)
        
        if result.get("final_status") == "completed":
            job.generated_resumes += 1
            
        _status(db, job, "Completed", {"completed_at": datetime.now(timezone.utc)})

    except Exception as e:
        logger.error(f"Single Pipeline failed: {e}", exc_info=True)
        try:
            _status(db, job, "Failed", {"completed_at": datetime.now(timezone.utc)})
        except:
            pass
    finally:
        db.close()
    
    logger.info(f"Single Pipeline FINISHED — Job ID: {job_id}")

async def process_single_job(db, tailoring_job, raw_job_data: dict, master_resume: MasterResume, resume_context: dict, resume_generator=None, bypass_yoe: bool = False) -> bool:
    from backend.models.core import MasterProfile
    mp = db.query(MasterProfile).first()
    mp_dict = mp.model_dump() if hasattr(mp, "model_dump") else mp.__dict__ if mp else {}
    if 'work_experience' in mp_dict and not 'workExperience' in mp_dict:
        mp_dict['workExperience'] = mp_dict['work_experience']
    if 'contact_info' in mp_dict and not 'contactInfo' in mp_dict:
        mp_dict['contactInfo'] = mp_dict['contact_info']
    if 'target_titles' in mp_dict and not 'targetTitles' in mp_dict:
        mp_dict['targetTitles'] = mp_dict['target_titles']
        
    resume_context["hash"] = master_resume.hash
    resume_context["parsed_text"] = master_resume.parsed_text
    
    initial_state = {
        "job_id": tailoring_job.id,
        "master_profile": mp_dict,
        "resume_context": resume_context,
        "raw_job_data": raw_job_data,
        "model_pref": tailoring_job.selected_model,
        "bypass_yoe": bypass_yoe,
        "retry_count": 0
    }
    
    result = compiled_graph.invoke(initial_state)
    return result.get("final_status") == "completed"

async def run_tailoring_pipeline(job_id: str):
    logger.info(f"{'='*60}\nPipeline START — Job ID: {job_id}\n{'='*60}")
    db = SessionLocal()
    try:
        job = tailoring_job_repo.get(db, job_id)
        if not job:
            return

        _status(db, job, "Preparing", {"started_at": datetime.now(timezone.utc)})

        master_resume = db.query(MasterResume).order_by(MasterResume.created_at.desc()).first()
        if not master_resume:
            logger.error("No master resume found. Cannot tailor.")
            _status(db, job, "Failed", {"completed_at": datetime.now(timezone.utc)})
            return
            
        _status(db, job, "Scraping via Apify")
        apify = ApifyClient()
        scraped_data = apify.scrape_linkedin_jobs(
            role=job.target_role, 
            location=job.location, 
            count=job.requested_jobs,
            posted_within=job.posted_within
        )
        
        job.scanned_jobs = len(scraped_data)
        db.commit()
        
        if not scraped_data:
            _status(db, job, "Completed", {"completed_at": datetime.now(timezone.utc)})
            return

        _status(db, job, "Tailoring")
        
        from celery import group
        from backend.celery_app import process_resume_task
        
        celery_tasks = [process_resume_task.s(job.id, raw_job) for raw_job in scraped_data]
        if celery_tasks:
            result = group(celery_tasks).apply_async()
            while not result.ready():
                await asyncio.sleep(2)
                db.refresh(job)
                
        _status(db, job, "Completed", {"completed_at": datetime.now(timezone.utc)})
    except Exception as e:
        logger.error(f"Pipeline crashed: {e}", exc_info=True)
        if 'job' in locals() and job:
            _status(db, job, "Failed", {"completed_at": datetime.now(timezone.utc)})
    finally:
        db.close()

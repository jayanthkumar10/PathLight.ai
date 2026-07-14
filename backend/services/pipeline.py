"""
Pathlight AI Engine — Main Processing Pipeline (Deterministic Version)
"""
import logging
import uuid
import os
import time
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from backend.database import SessionLocal
from backend.repositories.job_repo import tailoring_job_repo, application_repo
from backend.models.resume import MasterResume
from backend.models.job import ScrapedJob, JDIntelligenceCache, EvidenceMap as DBEvidenceMap, Application, TailoringJob
from backend.schemas.job import TailoringJobUpdate

from backend.services.scraper.apify_client import ApifyClient
from backend.services.engine.job_normalizer import normalize_apify_job
from backend.services.engine.suitability_filter import check_job_suitability
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
    logger.info(f"[Pipeline] Job {job.id[:8]}... -> {status}")

async def run_single_tailoring_pipeline(job_id: str, jd_text: str, job_url: str):
    logger.info(f"{'='*60}\nSingle Pipeline START — Job ID: {job_id}\n{'='*60}")

    db = SessionLocal()
    try:
        job = tailoring_job_repo.get(db, job_id)
        if not job:
            return

        _status(db, job, "Preparing", {"started_at": datetime.now(timezone.utc)})

        # Stage 1: Resume Context
        master_resume = db.query(MasterResume).order_by(MasterResume.created_at.desc()).first()
        if not master_resume:
            logger.error("No master resume found. Cannot tailor.")
            _status(db, job, "Failed", {"completed_at": datetime.now(timezone.utc)})
            return
            
        resume_context = get_resume_context(db, master_resume)

        # Stage 2: Extract details
        _status(db, job, "Extracting Details")
        metadata = extract_jd_metadata(jd_text)
        
        job.scanned_jobs = 1
        db.commit()

        # Construct a mock dictionary for process_single_job
        raw_job_data = {
            "title": metadata.job_title,
            "company": metadata.company,
            "location": metadata.location,
            "employmentType": metadata.employment_type,
            "salaryRange": metadata.salary_range,
            "url": job_url or "",
            "descriptionText": jd_text,
            "id": f"single_{job_id}" # dummy apify_id
        }

        _status(db, job, "Tailoring")
        
        resume_generator = ResumeGenerator()
        
        # Execute the single job
        success = await process_single_job(
            db, job, raw_job_data, master_resume, resume_context, resume_generator, bypass_yoe=True
        )
        
        if success:
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

async def process_single_job(db, tailoring_job, raw_job_data: dict, master_resume: MasterResume, resume_context: dict, resume_generator, bypass_yoe: bool = False) -> bool:
    """Processes one scraped job through the 14-step deterministic pipeline."""
    # Step 0: Deduplication Check
    apify_id = raw_job_data.get("id")
    if apify_id:
        existing_job = db.query(ScrapedJob).filter(ScrapedJob.apify_id == apify_id).first()
        if existing_job:
            logger.info(f"Skipping duplicate job (already processed): {apify_id}")
            return False

    # Step 1: Normalize
    norm_job = normalize_apify_job(raw_job_data)
    
    # Save ScrapedJob
    scraped = ScrapedJob(
        id=str(uuid.uuid4()),
        tailoring_job_id=tailoring_job.id,
        apify_id=raw_job_data.get("id"),
        url=norm_job.apply_url,
        raw_html=raw_job_data.get("descriptionText", ""),
        normalized_json=norm_job.model_dump(),
        raw_data=raw_job_data
    )
    db.add(scraped)
    db.flush() # flush to get scraped.id
    
    # Create Draft Application immediately so it shows up in UI
    app = Application(
        id=str(uuid.uuid4()),
        tailoring_job_id=tailoring_job.id,
        scraped_job_id=scraped.id,
        job_title=norm_job.title,
        company=norm_job.company,
        location=norm_job.location,
        apply_link=norm_job.apply_url,
        application_status="processing"
    )
    db.add(app)
    db.commit()
    
    # Step 2: Suitability Filter (Bypassed if explicitly requested, like in single tailor flow)
    if not bypass_yoe:
        candidate_summary = resume_context.get("profile_summary", "Candidate")
        min_conf = getattr(tailoring_job, "min_confidence", 55)
        passed, reason, score = check_job_suitability(norm_job, candidate_summary, min_confidence=min_conf, model=tailoring_job.selected_model)
        app.match_confidence = score
        if not passed:
            logger.info(f"Skipping {norm_job.title} - Suitability Filter ({score}%): {reason}")
            app.application_status = "Rejected"
            app.missing_keywords = f"Rejected by Suitability Filter ({score}%): {reason}"
            db.commit()
            return False
        
        # If passed, save the score anyway
        db.commit()
        
    db.query(TailoringJob).filter(TailoringJob.id == tailoring_job.id).update(
        {"matched_jobs": TailoringJob.matched_jobs + 1},
        synchronize_session=False
    )
    db.commit()
        
    # Step 3: JD Intelligence
    jd_hash = hashlib.sha256((norm_job.title + norm_job.description_text).encode()).hexdigest()
    
    jd_cache = db.query(JDIntelligenceCache).filter(JDIntelligenceCache.jd_hash == jd_hash).first()
    if jd_cache:
        jd_intel = jd_cache.extracted_skills
        logger.info("Using cached JD Intelligence")
    else:
        # Deterministic extraction
        extraction_obj = extract_jd_intelligence(norm_job.description_text)
        jd_intel = extraction_obj.model_dump()
        jd_cache = JDIntelligenceCache(
            jd_hash=jd_hash,
            extracted_skills=jd_intel,
            required_yoe=norm_job.yoe_required
        )
        db.add(jd_cache)
        db.commit()

    # Step 5: Evidence Mapper
    resume_hash = master_resume.hash
    evidence_cache = db.query(DBEvidenceMap).filter(
        DBEvidenceMap.jd_hash == jd_hash,
        DBEvidenceMap.resume_hash == resume_hash
    ).first()
    
    if evidence_cache:
        evidence_dict = evidence_cache.evidence_json
        rewrite_plan_dict = evidence_cache.rewrite_plan_json
        logger.info("Using cached Evidence Map & Rewrite Plan")
    else:
        from backend.services.engine.evidence_mapper import map_evidence, GapAnalysis
        from backend.services.engine.jd_intelligence import JDExtraction
        
        extraction_model = JDExtraction(**jd_intel)
        gap_obj = map_evidence(extraction_model, resume_context)
        
        evidence_dict = gap_obj.model_dump()
        rewrite_plan_dict = {}  # No longer used, but kept in DB schema for now
        
        e_map = DBEvidenceMap(
            id=str(uuid.uuid4()),
            resume_hash=resume_hash,
            jd_hash=jd_hash,
            evidence_json=evidence_dict,
            rewrite_plan_json=rewrite_plan_dict
        )
        db.add(e_map)
        db.commit()

    # Steps 7-9: Generation (Single Pass, No Evaluator Loop)
    from backend.services.engine.jd_intelligence import JDExtraction
    from backend.services.engine.evidence_mapper import GapAnalysis
    
    start_time = time.time()
    raw_resume_text = master_resume.parsed_text or ""
    
    try:
        from backend.models.core import MasterProfile
        master_profile = db.query(MasterProfile).first()

        logger.info(f"Generating resume for {norm_job.company}...")
        # Step 7: ONE LLM Call
        html, prompt_used = resume_generator.generate_html(
            raw_resume_text,
            resume_context, 

            norm_job, 
            JDExtraction(**jd_intel), 
            GapAnalysis(**evidence_dict),
            master_profile=master_profile,
            model_preference=tailoring_job.selected_model,
            feedback="" # No toxic feedback
        )
        
        # Step 10: ATS Evaluator (For UI Score Only, No Retries)
        missing_for_eval = GapAnalysis(**evidence_dict).missing_hard_skills + GapAnalysis(**evidence_dict).missing_technical_skills
        eval_result = evaluate_ats_score(html, missing_for_eval)
        best_score = eval_result.overall_ats_score
        best_feedback = eval_result.feedback
        best_html = html
        best_prompt = prompt_used
        
        logger.info(f"Generation complete. ATS Score: {best_score}")
        
    except Exception as e:
        logger.error(f"Generation failure: {e}", exc_info=True)
        app.application_status = "failed"
        db.commit()
        return False

    # Step 11: PDF Generation & Validation
    try:
        pdf_path = generate_and_validate_pdf(best_html, app.job_title, app.company)
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        app.application_status = "failed"
        db.commit()
        return False
        
    gen_time = time.time() - start_time
    
    # Update Application
    app.prompt_used = best_prompt
    app.generated_html = best_html
    app.generated_resume_path = pdf_path
    app.ats_score = best_score
    app.fit_score = best_score
    app.generation_time = gen_time
    app.missing_keywords = best_feedback
    app.application_status = "completed"
    db.commit()
    
    logger.info(f"Successfully finished job tailoring: {app.job_title} at {app.company}")
    return True

async def run_tailoring_pipeline(job_id: str):
    logger.info(f"{'='*60}\nPipeline START — Job ID: {job_id}\n{'='*60}")

    db = SessionLocal()
    try:
        job = tailoring_job_repo.get(db, job_id)
        if not job:
            return

        _status(db, job, "Preparing", {"started_at": datetime.now(timezone.utc)})

        # Stage 1: Resume Context
        master_resume = db.query(MasterResume).order_by(MasterResume.created_at.desc()).first()
        if not master_resume:
            logger.error("No master resume found. Cannot tailor.")
            _status(db, job, "Failed", {"completed_at": datetime.now(timezone.utc)})
            return
            
        resume_context = get_resume_context(db, master_resume)

        # Stage 2: Scrape LinkedIn
        _status(db, job, "Scraping")
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
            logger.error("No jobs found from Apify.")
            _status(db, job, "Completed", {"completed_at": datetime.now(timezone.utc)})
            return

        _status(db, job, "Tailoring")
        
        resume_generator = ResumeGenerator()
        
        # Async Fan-out execution via Celery
        from celery import group
        from backend.celery_app import process_resume_task
        import asyncio
        
        celery_tasks = [process_resume_task.s(job.id, raw_job) for raw_job in scraped_data]
        if celery_tasks:
            result = group(celery_tasks).apply_async()
            
            # Poll until all Celery workers finish their jobs
            while not result.ready():
                await asyncio.sleep(2)
                # Refresh job from DB to get the latest generated_resumes count
                db.refresh(job)
                
        _status(db, job, "Completed", {"completed_at": datetime.now(timezone.utc)})

    except Exception as e:
        logger.error(f"Pipeline crashed: {e}", exc_info=True)
        if job:
            _status(db, job, "Failed", {"completed_at": datetime.now(timezone.utc)})
    finally:
        db.close()

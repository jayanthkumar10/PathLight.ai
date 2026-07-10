import json
import logging
from typing import Dict, Any
from backend.services.llm.mcp import LLMClient

logger = logging.getLogger(__name__)

def get_resume_context(db, master_resume) -> Dict[str, Any]:
    """
    Step 4: Resume Context Engine.
    Fetches the cached master resume JSON. If critical elements (skills, verbs) are missing,
    it hydrates them using an LLM and saves them back to the database.
    """
    if not master_resume:
        raise ValueError("No master resume provided")
        
    try:
        # parsed_json is expected to be a dictionary or a JSON string
        if isinstance(master_resume.parsed_json, str):
            cached = json.loads(master_resume.parsed_json)
        elif isinstance(master_resume.parsed_json, dict):
            cached = master_resume.parsed_json
        else:
            cached = {}
    except Exception:
        cached = {}

    needs_hydration = False
    
    current_title = cached.get("current_title", "")
    hard_skills = [s.strip() for s in (master_resume.hard_skills or "").split(",") if s.strip()]
    soft_skills = [s.strip() for s in (master_resume.soft_skills or "").split(",") if s.strip()]
    tech_skills = [s.strip() for s in (master_resume.technical_skills or "").split(",") if s.strip()]
    action_verbs = [v.strip() for v in (master_resume.action_verbs or "").split(",") if v.strip()]

    if not hard_skills or not soft_skills or not action_verbs or not current_title:
        logger.info(f"Master Resume {master_resume.id} is missing structured data. Hydrating via LLM...")
        needs_hydration = True
        
        llm = LLMClient()
        sys_prompt = "You are an expert resume parser. Extract the following from the resume text into a strict JSON object: 'current_title' (string), 'hard_skills' (list of strings), 'soft_skills' (list of strings), 'technical_skills' (list of strings), 'action_verbs' (list of strings). Output ONLY valid JSON."
        user_prompt = f"Resume Text:\n{master_resume.parsed_text[:10000]}"
        
        try:
            res = llm.generate_text(sys_prompt, user_prompt, response_mime_type="application/json")
            
            clean_res = res.strip()
            if clean_res.startswith("```"):
                lines = clean_res.split('\n')
                if len(lines) > 1 and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_res = "\n".join(lines).strip()
                
            data = json.loads(clean_res)
            
            current_title = data.get("current_title", current_title)
            hard_skills = data.get("hard_skills", hard_skills)
            soft_skills = data.get("soft_skills", soft_skills)
            tech_skills = data.get("technical_skills", tech_skills)
            action_verbs = data.get("action_verbs", action_verbs)
            
            # Update DB
            cached["current_title"] = current_title
            master_resume.parsed_json = json.dumps(cached)
            master_resume.hard_skills = ",".join(hard_skills)
            master_resume.soft_skills = ",".join(soft_skills)
            master_resume.technical_skills = ",".join(tech_skills)
            master_resume.action_verbs = ",".join(action_verbs)
            
            db.commit()
            logger.info("Successfully hydrated and saved Master Resume structured data.")
        except Exception as e:
            logger.error(f"Failed to hydrate Master Resume: {e}")
        
    # Reconstruct the structured Resume Context
    resume_context = {
        "candidate_name": cached.get("candidate_name", "Candidate"),
        "current_title": current_title,
        "contact_info": cached.get("contact_info", ""),
        "years_of_experience": cached.get("years_of_experience", 0),
        "education": cached.get("education", ""),
        "companies": cached.get("companies", []),
        "hard_skills": hard_skills,
        "soft_skills": soft_skills,
        "technical_skills": tech_skills,
        "action_verbs": action_verbs,
    }
    
    return resume_context

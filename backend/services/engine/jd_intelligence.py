import json
import logging
import re
from typing import List
from pydantic import BaseModel, Field
from backend.services.llm.mcp import LLMClient

logger = logging.getLogger(__name__)

class JDExtraction(BaseModel):
    job_title: str = Field(default="")
    hard_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    action_verbs: List[str] = Field(default_factory=list)

def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}

def extract_jd_intelligence(jd_text: str) -> JDExtraction:
    """
    Step 3: JD Intelligence extraction using LLM for accurate context parsing.
    Returns a strict JSON format matching JDExtraction.
    """
    logger.info("Extracting JD intelligence via LLM...")
    llm = LLMClient()
    sys_prompt = (
        "You are an expert technical recruiter and resume ATS system. "
        "Extract the following from the Job Description into a strict JSON object: "
        "'job_title' (string), 'hard_skills' (list of strings), 'soft_skills' (list of strings), "
        "'technical_skills' (list of strings), 'action_verbs' (list of action verbs used in responsibilities). "
        "Output ONLY valid JSON."
    )
    user_prompt = f"Job Description:\n{jd_text[:10000]}"
    
    try:
        res = llm.generate_text(sys_prompt, user_prompt, response_mime_type="application/json", agent_name="JDExtractionNode")
        data = _extract_json(res)
        
        return JDExtraction(
            job_title=data.get("job_title", ""),
            hard_skills=data.get("hard_skills", []),
            soft_skills=data.get("soft_skills", []),
            technical_skills=data.get("technical_skills", []),
            action_verbs=data.get("action_verbs", [])
        )
    except Exception as e:
        logger.error(f"JD LLM Extraction failed: {e}")
        return JDExtraction()

class JDMeta(BaseModel):
    job_title: str = Field(default="Unknown Role")
    company: str = Field(default="Unknown Company")
    location: str = Field(default="Not Specified")
    employment_type: str = Field(default="Full-time")
    salary_range: str = Field(default="Not Specified")

def extract_jd_metadata(jd_text: str) -> JDMeta:
    """
    Extracts the Job Title and Company from raw JD text.
    """
    logger.info("Extracting JD metadata (Title, Company) via LLM...")
    llm = LLMClient()
    sys_prompt = (
        "You are an expert technical recruiter. Extract the Job Title, Company Name, Location, Employment Type, "
        "and Salary Range from the following Job Description text. "
        "Return a strict JSON object with 'job_title', 'company', 'location', 'employment_type', and 'salary_range'. "
        "If you cannot find a field, use 'Unknown Role', 'Unknown Company', 'Not Specified', or 'Full-time' as appropriate. "
        "Output ONLY valid JSON."
    )
    user_prompt = f"Job Description:\n{jd_text[:5000]}"
    
    try:
        res = llm.generate_text(sys_prompt, user_prompt, response_mime_type="application/json", agent_name="JDMetaExtractionNode")
        data = _extract_json(res)
        
        return JDMeta(
            job_title=data.get("job_title", "Unknown Role") or "Unknown Role",
            company=data.get("company", "Unknown Company") or "Unknown Company",
            location=data.get("location", "Not Specified") or "Not Specified",
            employment_type=data.get("employment_type", "Full-time") or "Full-time",
            salary_range=data.get("salary_range", "Not Specified") or "Not Specified"
        )
    except Exception as e:
        logger.error(f"JD Meta LLM Extraction failed: {e}")
        return JDMeta()

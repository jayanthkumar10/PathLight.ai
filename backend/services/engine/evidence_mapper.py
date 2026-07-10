from typing import Dict, Any, List
from pydantic import BaseModel
from rapidfuzz import fuzz, process
from backend.services.engine.jd_intelligence import JDExtraction

class GapAnalysis(BaseModel):
    missing_hard_skills: List[str]
    missing_soft_skills: List[str]
    missing_technical_skills: List[str]
    missing_action_verbs: List[str]
    
    present_hard_skills: List[str]
    present_soft_skills: List[str]
    present_technical_skills: List[str]
    present_action_verbs: List[str]

def _categorize(jd_list: List[str], cand_list: List[str]):
    present = []
    missing = []
    cand_set = set(cand_list)
    
    for item in jd_list:
        match = process.extractOne(item, cand_set, scorer=fuzz.WRatio)
        if match and match[1] >= 85:
            present.append(item)
        else:
            missing.append(item)
    return present, missing

def map_evidence(jd_extract: JDExtraction, resume_context: Dict[str, Any]) -> GapAnalysis:
    """
    Step 5: Gap Analysis Engine.
    Compares the JD JSON against the Master Resume JSON arrays.
    """
    cand_hard = resume_context.get("hard_skills", [])
    cand_soft = resume_context.get("soft_skills", [])
    cand_tech = resume_context.get("technical_skills", [])
    cand_verbs = resume_context.get("action_verbs", [])
    
    p_hard, m_hard = _categorize(jd_extract.hard_skills, cand_hard)
    p_soft, m_soft = _categorize(jd_extract.soft_skills, cand_soft)
    p_tech, m_tech = _categorize(jd_extract.technical_skills, cand_tech)
    p_verbs, m_verbs = _categorize(jd_extract.action_verbs, cand_verbs)
    
    return GapAnalysis(
        missing_hard_skills=m_hard,
        missing_soft_skills=m_soft,
        missing_technical_skills=m_tech,
        missing_action_verbs=m_verbs,
        present_hard_skills=p_hard,
        present_soft_skills=p_soft,
        present_technical_skills=p_tech,
        present_action_verbs=p_verbs
    )

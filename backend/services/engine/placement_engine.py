from typing import Dict, Any, List
from .evidence_mapper import EvidenceMap
from pydantic import BaseModel

class RewritePlan(BaseModel):
    inject_summary: List[str]
    inject_skills: List[str]
    inject_experience: List[str]
    preserve: List[str]

def generate_placement_plan(evidence: EvidenceMap) -> RewritePlan:
    """
    Step 6: Deterministic Placement Engine.
    Decides exactly where each missing keyword should be injected.
    Produces a strict Rewrite Plan.
    """
    inject_summary = []
    inject_skills = []
    inject_experience = []
    
    # We heuristically assign skills based on their type. 
    # For MVP, we will try to place everything missing into Skills section, 
    # and a couple top ones into Summary.
    for i, skill in enumerate(evidence.missing):
        # The most important missing skills go to summary
        if i < 3:
            inject_summary.append(skill)
            
        # All technical/hard skills go to Skills block
        inject_skills.append(skill)
        
        # We also want to weave them into the experience bullets
        inject_experience.append(skill)
        
    return RewritePlan(
        inject_summary=inject_summary,
        inject_skills=inject_skills,
        inject_experience=inject_experience,
        preserve=evidence.already_present
    )

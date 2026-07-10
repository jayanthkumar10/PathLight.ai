import re
from rapidfuzz import fuzz, process
from pydantic import BaseModel
from typing import List, Optional

class ATSEvaluation(BaseModel):
    overall_ats_score: float
    keyword_coverage_score: float
    feedback: str

def evaluate_ats_score(html_content: str, missing_keywords: List[str]) -> ATSEvaluation:
    """
    Step 10: ATS Evaluator (Hybrid/Deterministic).
    Extracts text from HTML and checks if the missing keywords were successfully injected.
    Returns a score from 0-100.
    """
    # 1. Clean HTML to raw text
    clean_text = re.sub(r'<[^>]+>', ' ', html_content)
    clean_text = re.sub(r'\s+', ' ', clean_text).lower()
    
    if not missing_keywords:
        return ATSEvaluation(
            overall_ats_score=100.0,
            keyword_coverage_score=100.0,
            feedback="No missing keywords to inject. Perfect match."
        )
        
    found_count = 0
    missing_after_rewrite = []
    
    for kw in missing_keywords:
        # Simple substring check first
        if kw.lower() in clean_text:
            found_count += 1
            continue
            
        # Fuzzy match across tokens
        tokens = clean_text.split()
        match = process.extractOne(kw.lower(), tokens, scorer=fuzz.WRatio)
        if match and match[1] >= 85:
            found_count += 1
        else:
            missing_after_rewrite.append(kw)
            
    coverage_score = (found_count / len(missing_keywords)) * 100
    
    # Penalize if it completely hallucinated or generated too little text
    length_penalty = 0
    if len(clean_text) < 500:
        length_penalty = 50
        
    overall_score = max(0, coverage_score - length_penalty)
    
    feedback = ""
    if missing_after_rewrite:
        feedback = f"You failed to include these mandatory keywords: {', '.join(missing_after_rewrite)}. You MUST inject them naturally into the experience bullets or skills section."
    
    return ATSEvaluation(
        overall_ats_score=overall_score,
        keyword_coverage_score=coverage_score,
        feedback=feedback
    )

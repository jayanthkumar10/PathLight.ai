import logging
import json
from .job_normalizer import NormalizedJob
from backend.services.llm.mcp import LLMClient

logger = logging.getLogger(__name__)

def check_job_suitability(job: NormalizedJob, candidate_summary: str, min_confidence: int = 55, model: str = "gemini-1.5-flash-latest") -> tuple[bool, str, int]:
    """
    Intelligent Suitability filter using LLM.
    Evaluates the full JD against the candidate's profile summary.
    Returns (accepted: bool, reason: str, confidence_score: int).
    """
    try:
        llm = LLMClient()
        prompt = f"""
        You are an expert technical recruiter evaluating a candidate's fit for a job.
        
        Candidate Profile Summary:
        {candidate_summary}
        
        Job Details:
        Title: {job.title}
        Company: {job.company}
        Years of Experience Required: {job.yoe_required if job.yoe_required is not None else 'Not explicitly stated'}
        
        Job Description:
        {job.description_text[:6000]}
        
        Task: 
        Evaluate if this candidate is a realistic match for this role based on their skills, experience, and the job requirements.
        Output a confidence score between 0 and 100.
        
        Rules for Confidence Score:
        - 80-100: Strong match. Candidate meets all core requirements and YOE.
        - 55-79: Potential match. Candidate meets most requirements, or has a slight YOE gap (e.g. 1-2 years short) but strong relevant skills.
        - 0-54: Poor match. Major gaps in core skills or massive YOE gap (e.g., requires 10 years, candidate has 2).
        
        Output format: Return ONLY a JSON object with this exact schema:
        {{
            "confidence_score": integer between 0 and 100,
            "reason": "Brief 1-sentence explanation of the score"
        }}
        Do NOT wrap in markdown code blocks. Just raw JSON.
        """
        
        response = llm.generate_text(
            system_prompt="You are an expert technical recruiter.",
            user_prompt=prompt,
            model_preference=model,
            response_mime_type="application/json",
            agent_name="SuitabilityFilterNode"
        )
        
        # Clean response
        clean_res = response.strip()
        if clean_res.startswith("```json"): clean_res = clean_res[7:]
        elif clean_res.startswith("```"): clean_res = clean_res[3:]
        if clean_res.endswith("```"): clean_res = clean_res[:-3]
        clean_res = clean_res.strip()
        
        data = json.loads(clean_res)
        
        score = int(data.get("confidence_score", 0))
        reason = str(data.get("reason", "LLM Evaluation"))
        passed = score >= min_confidence
        
        return passed, reason, score
        
    except Exception as e:
        logger.error(f"Suitability Filter failed: {e}")
        # If the LLM fails or hits a rate limit, return False with score 0 to prevent wasting tokens
        # on a full rewrite when we can't verify suitability.
        return False, f"LLM Filter failed: {str(e)}", 0

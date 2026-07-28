import logging
import json
from .job_normalizer import NormalizedJob
from backend.services.llm.mcp import LLMClient

logger = logging.getLogger(__name__)

def passes_yoe_filter(job: NormalizedJob, candidate_yoe: int) -> tuple[bool, str]:
    """
    Step 2: Intelligent YOE filter using LLM.
    Returns (accepted: bool, reason: str).
    """
    # Quick deterministic pass if no YOE required
    if job.yoe_required is None:
        return True, "No explicit YOE requirement found -> accepted"
        
    try:
        llm = LLMClient()
        prompt = f"""
        You are a tech recruiter evaluating a candidate's Years of Experience (YOE) against a Job Description.
        Candidate YOE: {candidate_yoe} years
        Required YOE: {job.yoe_required} years
        
        Job Title: {job.title}
        Company: {job.company}
        Description Snippet: {job.description_text[:2000]}
        
        Task: Decide if the candidate's YOE is a realistic match for this role. 
        Rules:
        - If the candidate is within 2-3 years of the requirement, they can often still qualify if they have strong skills.
        - If the gap is massive (e.g. they have 2 years and it requires 10 for a Principal role), reject.
        
        Output format: Return ONLY a JSON object with this exact schema:
        {{
            "passed": true or false,
            "reason": "Brief 1-sentence explanation"
        }}
        Do NOT wrap in markdown code blocks. Just raw JSON.
        """
        
        response = llm.generate_text(
            system_prompt="You are an expert technical recruiter.",
            user_prompt=prompt,
            model_preference="mistral-small-latest",
            response_mime_type="application/json",
            agent_name="YOEFilterNode"
        )
        
        # Clean response
        clean_res = response.strip()
        if clean_res.startswith("```json"): clean_res = clean_res[7:]
        elif clean_res.startswith("```"): clean_res = clean_res[3:]
        if clean_res.endswith("```"): clean_res = clean_res[:-3]
        clean_res = clean_res.strip()
        
        data = json.loads(clean_res)
        
        return bool(data.get("passed", False)), str(data.get("reason", "LLM Evaluation"))
        
    except Exception as e:
        logger.error(f"YOE LLM Filter failed, falling back to deterministic: {e}")
        # Fallback to deterministic
        threshold = candidate_yoe + 3
        if job.yoe_required > threshold:
            return False, f"Requires {job.yoe_required}y, candidate has {candidate_yoe}y (threshold: {threshold}y)"
        return True, f"Requires {job.yoe_required}y -> within threshold ({threshold}y)"

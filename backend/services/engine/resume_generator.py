import logging
import json
from backend.services.llm.mcp import LLMClient
from backend.services.engine.prompt_builder import build_rewrite_prompt
from backend.services.engine.template_constants import RESUME_TEMPLATE_HTML

logger = logging.getLogger(__name__)

class ResumeGenerator:
    """
    Step 9: Orchestrates the ONE LLM rewrite call and JSON template injection.
    """
    def __init__(self):
        self.llm_client = LLMClient()

    def generate_html(self, 
                      raw_resume_text: str,
                      resume_context, 
                      job, 
                      jd_extraction, 
                      gap_analysis, 
                      model_preference="gemini-2.5-flash",
                      feedback="") -> tuple[str, str]:
        """
        Executes the rewrite prompt and returns (generated_html, prompt_used)
        """
        sys_prompt, user_prompt = build_rewrite_prompt(
            raw_resume_text, resume_context, job, jd_extraction, gap_analysis, feedback
        )
        
        logger.info(f"Triggering ONE LLM call for {job.title} at {job.company}...")
        
        raw_output = self.llm_client.generate_text(sys_prompt, user_prompt, model_preference)
        
        # Strip markdown fences if present
        clean_output = raw_output.strip()
        if clean_output.startswith("```json"):
            clean_output = clean_output[7:]
        elif clean_output.startswith("```"):
            clean_output = clean_output[3:]
        if clean_output.endswith("```"):
            clean_output = clean_output[:-3]
            
        clean_output = clean_output.strip()
        
        try:
            data = json.loads(clean_output)
            
            html_content = RESUME_TEMPLATE_HTML.format(
                subtitle=data.get("subtitle", "AI Engineer"),
                professional_summary=data.get("professional_summary", ""),
                technical_skills=data.get("technical_skills", ""),
                tcs_role=data.get("tcs_role", "AI Engineer"),
                tcs_bullets=data.get("tcs_bullets", ""),
                project_1_bullets=data.get("project_1_bullets", ""),
                project_2_bullets=data.get("project_2_bullets", ""),
                achievements_bullets=data.get("achievements_bullets", "")
            )
            return html_content, (sys_prompt + "\n\n" + user_prompt)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM: {clean_output}")
            raise ValueError(f"LLM did not return valid JSON: {e}")
        except KeyError as e:
            logger.error(f"Missing key in JSON for format: {e}")
            raise ValueError(f"LLM JSON missing required formatting key: {e}")

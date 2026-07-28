import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import SessionLocal
from backend.models.core import AgentRun, AgentMetric
from backend.services.llm.mcp import LLMClient
from backend.services.llmops_client import LLMOpsClient

logger = logging.getLogger(__name__)

class Evaluator:
    """
    Handles calculating quantitative and qualitative metrics for AgentRuns.
    Uses LLM-as-a-judge for Hallucination, Groundedness, Helpfulness, Toxicity, Completeness, and Consistency.
    """
    
    def __init__(self):
        self.llm = LLMClient()
        
    def evaluate_run_async(self, run_id: str, original_resume: str, generated_resume: str, jd_text: str):
        """
        Calculates all quality metrics asynchronously and updates the AgentRun row.
        """
        try:
            metrics = self._run_llm_judge(original_resume, generated_resume, jd_text)
            LLMOpsClient.record_metrics_async(run_id, metrics)
            self._update_aggregate_kpis()
        except Exception as e:
            logger.error(f"Failed to evaluate run {run_id}: {e}")

    def _run_llm_judge(self, original_resume: str, generated_resume: str, jd_text: str) -> Dict[str, Any]:
        """
        Uses Mistral to act as a judge and score the generated resume.
        """
        sys_prompt = """
        You are an expert AI evaluator grading the quality of an AI-tailored resume.
        You will receive the Candidate's Original Resume, the Target Job Description (JD), and the AI-Generated Tailored Resume.
        
        Score the AI-Generated Tailored Resume on the following metrics from 0 to 100:
        1. "hallucination": 0 = many fabricated skills/experience not in original resume, 100 = completely factual based on original.
        2. "groundedness": 100 = every claim in the generated resume is backed by the original resume.
        3. "helpfulness": 100 = highly effective at targeting the JD.
        4. "toxicity": 0 = toxic/inappropriate, 100 = completely safe and professional.
        5. "completeness": 100 = addresses all possible matching requirements from the JD.
        6. "consistency": 100 = formatting and tone are consistent throughout.
        
        Output ONLY a JSON object with integer scores:
        {
            "hallucination": 100,
            "groundedness": 95,
            "helpfulness": 90,
            "toxicity": 100,
            "completeness": 85,
            "consistency": 90
        }
        """
        
        user_prompt = f"""
        --- ORIGINAL RESUME ---
        {original_resume[:4000]}
        
        --- JOB DESCRIPTION ---
        {jd_text[:4000]}
        
        --- GENERATED RESUME ---
        {generated_resume[:4000]}
        """
        
        try:
            # We use a capable model for evaluation
            res = self.llm.generate_text(
                system_prompt=sys_prompt, 
                user_prompt=user_prompt, 
                model_preference="mistral-large-latest", 
                response_mime_type="application/json",
                agent_name="EvaluationJudgeNode"
            )
            
            clean_res = res.strip()
            if clean_res.startswith("```"):
                lines = clean_res.split('\n')
                if len(lines) > 1 and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_res = "\n".join(lines).strip()
                
            data = json.loads(clean_res)
            return {
                "hallucination": data.get("hallucination", 0),
                "groundedness": data.get("groundedness", 0),
                "helpfulness": data.get("helpfulness", 0),
                "toxicity": data.get("toxicity", 100),
                "completeness": data.get("completeness", 0),
                "consistency": data.get("consistency", 0)
            }
        except Exception as e:
            logger.error(f"LLM Judge failed: {e}")
            return {}

    def _update_aggregate_kpis(self):
        """
        Calculates and stores average KPIs like Success Rate, Average Cost, Tokens, Latency.
        """
        db: Session = SessionLocal()
        try:
            # Group by AgentName
            agent_names = [r[0] for r in db.query(AgentRun.agentName).distinct()]
            
            for agent in agent_names:
                runs = db.query(AgentRun).filter(AgentRun.agentName == agent).all()
                if not runs:
                    continue
                    
                total_runs = len(runs)
                successful_runs = sum(1 for r in runs if not r.error)
                retries = sum(r.retryCount for r in runs if r.retryCount is not None)
                total_cost = sum(r.cost for r in runs if r.cost is not None)
                total_tokens = sum(r.tokens for r in runs if r.tokens is not None)
                total_latency = sum(r.latency for r in runs if r.latency is not None)
                
                success_rate = int((successful_runs / total_runs) * 100) if total_runs > 0 else 0
                retry_percent = int((retries / total_runs) * 100) if total_runs > 0 else 0
                avg_cost = int(total_cost / successful_runs) if successful_runs > 0 else 0
                avg_tokens = int(total_tokens / successful_runs) if successful_runs > 0 else 0
                avg_latency = int(total_latency / successful_runs) if successful_runs > 0 else 0
                failure_percent = 100 - success_rate
                
                metric = AgentMetric(
                    agentName=agent,
                    successRate=success_rate,
                    retryPercent=retry_percent,
                    averageCost=avg_cost,
                    averageTokens=avg_tokens,
                    averageLatency=avg_latency,
                    failurePercent=failure_percent,
                    date=datetime.now(timezone.utc)
                )
                db.add(metric)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to update aggregate KPIs: {e}")
        finally:
            db.close()

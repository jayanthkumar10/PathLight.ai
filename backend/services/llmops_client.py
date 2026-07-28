import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.core import AgentRun
from backend.database import SessionLocal

logger = logging.getLogger(__name__)

# Try importing langfuse
try:
    from langfuse import Langfuse
    # We only initialize it if keys are present
    if settings.LANGFUSE_SECRET_KEY and settings.LANGFUSE_PUBLIC_KEY:
        langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL
        )
    else:
        langfuse = None
except ImportError:
    langfuse = None


class LLMOpsClient:
    """
    Client for LLM observability. Records structured events (AgentRun) 
    to local SQLite, and optionally to Langfuse if configured.
    """
    
    @staticmethod
    def log_agent_run(
        agent_name: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        output: str,
        latency_ms: int,
        tokens: int,
        cost: float,
        error: Optional[str] = None,
        retry_count: int = 0,
        trace_id: Optional[str] = None
    ) -> str:
        """
        Logs an individual LLM call/agent reasoning step.
        Returns the run ID.
        """
        run_id = str(uuid.uuid4())
        trace_id = trace_id or str(uuid.uuid4())
        
        # 1. Log to Local Database
        db: Session = SessionLocal()
        try:
            agent_run = AgentRun(
                runId=run_id,
                traceId=trace_id,
                agentName=agent_name,
                model=model,
                input=f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}",
                output=output,
                latency=latency_ms,
                tokens=tokens,
                # Convert cost to microcents or just store as int scaled up. 
                # For simplicity, assuming cost parameter is already scaled or we just store an int approximation.
                cost=int(cost * 1_000_000), 
                error=error,
                retryCount=retry_count
            )
            db.add(agent_run)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log AgentRun to local DB: {e}")
        finally:
            db.close()
            
        # 2. Log to Langfuse (if configured)
        if langfuse:
            try:
                langfuse.generation(
                    id=run_id,
                    trace_id=trace_id,
                    name=agent_name,
                    model=model,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    output=output,
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc), # Approximate
                    usage={
                        "total_tokens": tokens,
                        "cost": cost
                    },
                    level="ERROR" if error else "DEFAULT",
                    status_message=error
                )
            except Exception as e:
                logger.error(f"Failed to log AgentRun to Langfuse: {e}")
                
        return run_id
        
    @staticmethod
    def record_metrics_async(run_id: str, metrics: Dict[str, Any]):
        """
        Update the local AgentRun row with qualitative metrics (e.g. from LLM-as-a-judge).
        """
        db: Session = SessionLocal()
        try:
            run = db.query(AgentRun).filter(AgentRun.runId == run_id).first()
            if run:
                for k, v in metrics.items():
                    if hasattr(run, k):
                        setattr(run, k, v)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update AgentRun metrics: {e}")
        finally:
            db.close()

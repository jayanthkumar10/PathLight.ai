import time
import logging
import requests
from typing import Optional
from backend.core.config import settings
from backend.services.llmops_client import LLMOpsClient

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

class LLMClient:
    """
    Mistral-exclusive LLM Client with observability.
    """
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY
        if not self.mistral_key:
            logger.warning("MISTRAL_API_KEY is not set. LLM calls will fail.")

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        # Approximate pricing for Mistral (per 1M tokens)
        prices = {
            "mistral-large-latest": (2.0, 6.0),
            "mistral-small-latest": (0.2, 0.6),
            "open-mistral-nemo": (0.15, 0.15),
            "mistral-tiny": (0.15, 0.15)
        }
        in_price, out_price = prices.get(model, (0.2, 0.6))
        return (prompt_tokens / 1_000_000 * in_price) + (completion_tokens / 1_000_000 * out_price)

    def _call_mistral(self, system_prompt: str, user_prompt: str, model_preference: str, response_mime_type: str) -> dict:
        if not self.mistral_key:
            raise RuntimeError("MISTRAL_API_KEY is missing.")
            
        headers = {
            "Authorization": f"Bearer {self.mistral_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": model_preference,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 4096
        }
        
        if response_mime_type == "application/json":
            payload["response_format"] = {"type": "json_object"}

        start_time = time.time()
        resp = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=60)
        latency = int((time.time() - start_time) * 1000)
        
        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return {
                    "content": content,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "latency": latency
                }
            else:
                raise ValueError(f"Invalid Mistral response format: {data}")
        elif resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    delay = int(retry_after)
                    raise RuntimeError(f"Mistral Rate Limit. Retry-After: {delay}")
                except ValueError:
                    pass
            raise RuntimeError("Mistral Rate Limit (429 Too Many Requests)")
        else:
            raise RuntimeError(f"Mistral returned {resp.status_code}: {resp.text}")

    def generate_text(self, system_prompt: str, user_prompt: str, model_preference: str = "mistral-small-latest", response_mime_type: str = "text/plain", agent_name: str = "MistralAgent") -> str:
        """
        Generates text using Mistral models exclusively.
        Implements exponential backoff for rate limit resilience and logs the AgentRun.
        """
        max_attempts = 4
        
        # Override gemini or non-mistral models
        if "mistral" not in model_preference.lower():
            model_preference = "mistral-small-latest"
            
        for attempt in range(max_attempts):
            try:
                result = self._call_mistral(system_prompt, user_prompt, model_preference, response_mime_type)
                
                # Log success metrics
                cost = self._estimate_cost(model_preference, result["prompt_tokens"], result["completion_tokens"])
                LLMOpsClient.log_agent_run(
                    agent_name=agent_name,
                    model=model_preference,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    output=result["content"],
                    latency_ms=result["latency"],
                    tokens=result["total_tokens"],
                    cost=cost,
                    retry_count=attempt
                )
                
                return result["content"]
                
            except Exception as e:
                # Log failure metric for the attempt
                error_msg = str(e)
                wait_time = 2 ** attempt
                if "Retry-After: " in error_msg:
                    try:
                        wait_time = int(error_msg.split("Retry-After: ")[1])
                    except:
                        pass
                
                logger.warning(f"Mistral generation error (attempt {attempt+1}/{max_attempts}): {e}. Waiting {wait_time}s...")
                
                if attempt == max_attempts - 1:
                    LLMOpsClient.log_agent_run(
                        agent_name=agent_name,
                        model=model_preference,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        output="",
                        latency_ms=0,
                        tokens=0,
                        cost=0.0,
                        error=error_msg,
                        retry_count=attempt
                    )
                    raise RuntimeError(f"All {max_attempts} Mistral generation attempts failed: {error_msg}")
                    
                time.sleep(wait_time)

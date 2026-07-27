import os
import time
import logging
import requests
from typing import Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

class LLMClient:
    """
    Minimal MCP abstraction for the LLM.
    Purely a text-in, text-out interface that uses Mistral as primary and OpenRouter as fallback.
    """
    def __init__(self):
        self.openrouter_key = settings.OPEN_ROUTER_API_KEY
        self.mistral_key = settings.MISTRAL_API_KEY
        
        if not self.openrouter_key:
            logger.warning("OPEN_ROUTER_API_KEY is not set.")
        if not self.mistral_key:
            logger.warning("MISTRAL_API_KEY is not set.")

    def _call_mistral(self, system_prompt: str, user_prompt: str, model_preference: str, response_mime_type: str) -> str:
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

        resp = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=60)
        
        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
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

    def _call_openrouter(self, system_prompt: str, user_prompt: str, model_preference: str, response_mime_type: str) -> str:
        if not self.openrouter_key:
            raise RuntimeError("OPEN_ROUTER_API_KEY is missing.")

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://pathlight.ai",
            "X-Title": "Pathlight ATS"
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
            
        resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Invalid OpenRouter response format: {data}")
        elif resp.status_code == 429:
            raise RuntimeError("OpenRouter Rate Limit")
        else:
            raise RuntimeError(f"OpenRouter returned {resp.status_code}: {resp.text}")

    def generate_text(self, system_prompt: str, user_prompt: str, model_preference: str = "mistral-small-latest", response_mime_type: str = "text/plain") -> str:
        """
        Generates text using the preferred model. If Mistral fails, falls back to OpenRouter.
        Implements exponential backoff for rate limit resilience.
        """
        max_attempts = 4
        for attempt in range(max_attempts):
            try:
                # Route based on model prefix
                if "gemini" in model_preference.lower() or "mistral" in model_preference.lower():
                    # Map legacy Gemini calls to Mistral
                    if "gemini" in model_preference.lower() or model_preference.lower() == "mistral":
                        model_preference = "mistral-small-latest"
                        
                    try:
                        return self._call_mistral(system_prompt, user_prompt, model_preference, response_mime_type)
                    except Exception as e:
                        logger.error(f"Mistral generation failed: {e}. Falling back to OpenRouter...")
                        # Fallback to OpenRouter with a robust model
                        return self._call_openrouter(system_prompt, user_prompt, "google/gemma-4-31b-it:free", response_mime_type)
                else:
                    return self._call_openrouter(system_prompt, user_prompt, model_preference, response_mime_type)
                    
            except Exception as e:
                # Check if it's a specific Retry-After exception
                error_msg = str(e)
                wait_time = 2 ** attempt
                if "Retry-After: " in error_msg:
                    try:
                        wait_time = int(error_msg.split("Retry-After: ")[1])
                    except:
                        pass
                
                logger.warning(f"Network or generation error (attempt {attempt+1}/{max_attempts}): {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)

        raise RuntimeError(f"All {max_attempts} LLM generation attempts failed.")

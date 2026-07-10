import os
import time
import logging
import requests
from typing import Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

class LLMClient:
    """
    Step 8: Minimal MCP abstraction for the LLM.
    Purely a text-in, text-out interface that exclusively uses OpenRouter.
    """
    def __init__(self):
        self.openrouter_key = settings.OPEN_ROUTER_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY
        if not self.openrouter_key:
            logger.warning("OPEN_ROUTER_API_KEY is not set.")
        if not self.gemini_key:
            logger.warning("GEMINI_API_KEY is not set.")

    def _call_gemini(self, system_prompt: str, user_prompt: str, model_preference: str, response_mime_type: str) -> str:
        if not self.gemini_key:
            raise RuntimeError("GEMINI_API_KEY is missing.")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_preference}:generateContent?key={self.gemini_key}"
        
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [{
                "parts": [{"text": user_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192
            }
        }
        
        if response_mime_type == "application/json":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        resp = requests.post(url, json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                raise ValueError(f"Invalid Gemini response: {data}") from e
        else:
            raise RuntimeError(f"Gemini returned {resp.status_code}: {resp.text}")

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
            "max_tokens": 8192
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

    def generate_text(self, system_prompt: str, user_prompt: str, model_preference: str = "gemini-2.5-flash", response_mime_type: str = "text/plain") -> str:
        """
        Generates text using the preferred model. If Gemini fails, falls back to OpenRouter.
        Implements exponential backoff for rate limit resilience.
        """
        max_attempts = 4
        for attempt in range(max_attempts):
            try:
                # Route based on model prefix
                if "gemini" in model_preference.lower():
                    try:
                        return self._call_gemini(system_prompt, user_prompt, model_preference, response_mime_type)
                    except Exception as e:
                        logger.error(f"Gemini generation failed: {e}. Falling back to OpenRouter...")
                        # Fallback to OpenRouter with a robust model
                        return self._call_openrouter(system_prompt, user_prompt, "meta-llama/llama-3.3-70b-instruct:free", response_mime_type)
                else:
                    return self._call_openrouter(system_prompt, user_prompt, model_preference, response_mime_type)
                    
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"Network or generation error (attempt {attempt+1}/{max_attempts}): {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)

        raise RuntimeError(f"All {max_attempts} LLM generation attempts failed.")


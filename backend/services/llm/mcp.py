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
    Purely a text-in, text-out interface that exclusively uses OpenRouter and Gemini.
    Integrated with Langfuse for observability.
    """
    def __init__(self):
        self.openrouter_key = settings.OPEN_ROUTER_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY
        if not self.openrouter_key:
            logger.warning("OPEN_ROUTER_API_KEY is not set.")
        if not self.gemini_key:
            logger.warning("GEMINI_API_KEY is not set.")
            
        try:
            from langfuse import Langfuse
            self.langfuse = Langfuse()
            logger.info("Langfuse initialized successfully.")
        except Exception as e:
            logger.warning(f"Langfuse init failed (tracing disabled): {e}")
            self.langfuse = None

    def _call_gemini(self, system_prompt: str, user_prompt: str, model_preference: str, response_mime_type: str) -> tuple[str, dict]:
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
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                usage = data.get("usageMetadata", {})
                usage_dict = {
                    "input": usage.get("promptTokenCount", 0),
                    "output": usage.get("candidatesTokenCount", 0),
                    "total": usage.get("totalTokenCount", 0)
                }
                return content, usage_dict
            except (KeyError, IndexError) as e:
                raise ValueError(f"Invalid Gemini response: {data}") from e
        else:
            raise RuntimeError(f"Gemini returned {resp.status_code}: {resp.text}")

    def _call_openrouter(self, system_prompt: str, user_prompt: str, model_preference: str, response_mime_type: str) -> tuple[str, dict]:
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
                content = data["choices"][0]["message"]["content"]
                usage_raw = data.get("usage", {})
                usage_dict = {
                    "input": usage_raw.get("prompt_tokens", 0),
                    "output": usage_raw.get("completion_tokens", 0),
                    "total": usage_raw.get("total_tokens", 0)
                }
                return content, usage_dict
            else:
                raise ValueError(f"Invalid OpenRouter response format: {data}")
        elif resp.status_code == 429:
            raise RuntimeError("OpenRouter Rate Limit")
        else:
            raise RuntimeError(f"OpenRouter returned {resp.status_code}: {resp.text}")

    def generate_text(self, system_prompt: str, user_prompt: str, model_preference: str = "gemini-1.5-flash", response_mime_type: str = "text/plain", observation_name: str = "Resume Tailoring LLM") -> str:
        """
        Generates text using the preferred model. If Gemini fails, falls back to OpenRouter.
        Implements exponential backoff for rate limit resilience.
        """
        max_attempts = 4
        
        # Start a Langfuse generation object
        generation = None
        if self.langfuse:
            try:
                generation = self.langfuse.start_observation(
                    name=observation_name,
                    as_type="generation",
                    model=model_preference,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
            except Exception as e:
                logger.error(f"Langfuse trace start failed: {e}")

        for attempt in range(max_attempts):
            try:
                # Route based on model prefix
                if "gemini" in model_preference.lower():
                    if model_preference.lower() == "gemini":
                        model_preference = "gemini-1.5-flash"
                    try:
                        content, usage = self._call_gemini(system_prompt, user_prompt, model_preference, response_mime_type)
                    except Exception as e:
                        logger.error(f"Gemini generation failed: {e}. Falling back to OpenRouter...")
                        # Fallback to OpenRouter with a robust model
                        fallback_model = "meta-llama/llama-3.3-70b-instruct:free"
                        if generation:
                            try:
                                generation.update(model=fallback_model)
                            except Exception:
                                pass
                        content, usage = self._call_openrouter(system_prompt, user_prompt, fallback_model, response_mime_type)
                else:
                    content, usage = self._call_openrouter(system_prompt, user_prompt, model_preference, response_mime_type)
                
                # End generation if successful
                if generation:
                    try:
                        generation.update(
                            output=content,
                            usage_details=usage
                        )
                        generation.end()
                        self.langfuse.flush() # Ensure it's sent immediately for fast debugging
                    except Exception as e:
                        logger.error(f"Langfuse trace end failed: {e}")
                
                return content
                    
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"Network or generation error (attempt {attempt+1}/{max_attempts}): {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)

        if generation:
            try:
                generation.end(level="ERROR", status_message="All attempts failed")
                self.langfuse.flush()
            except Exception:
                pass
                
        raise RuntimeError(f"All {max_attempts} LLM generation attempts failed.")


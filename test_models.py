"""Quick test of new OpenRouter model IDs"""
import os, requests
from dotenv import load_dotenv
load_dotenv()

key = os.getenv('OPEN_ROUTER_API_KEY', '')
models_to_test = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
]

for model in models_to_test:
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say OK in JSON: {\"status\": \"ok\"}"}],
                "max_tokens": 20,
                "temperature": 0
            },
            timeout=30
        )
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            print(f"OK   {model}: {content[:50]}")
        else:
            print(f"FAIL {model}: HTTP {r.status_code}")
    except Exception as e:
        print(f"ERR  {model}: {e}")

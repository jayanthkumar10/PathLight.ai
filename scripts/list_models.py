import os, requests
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('OPEN_ROUTER_API_KEY','')
r = requests.get('https://openrouter.ai/api/v1/models', headers={'Authorization': f'Bearer {key}'}, timeout=15)
models = r.json().get('data', [])
free = [m for m in models if str(m.get('pricing', {}).get('prompt','1')) == '0']
print(f'Total free models: {len(free)}')
for m in sorted(free, key=lambda x: x.get('id','')):
    ctx = m.get('context_length', 0)
    print(f"  {m['id']}  (ctx={ctx})")

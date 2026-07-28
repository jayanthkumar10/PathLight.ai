import requests
import json
import time
import sys

payload = {
    "title": "Agentic AI Engineer",
    "company": "Talentgigs",
    "location": "Hyderabad, Telangana, India",
    "url": "https://www.linkedin.com/jobs/view/1444306161/",
    "descriptionText": "This is a mock description for an Agentic AI Engineer. We are looking for someone who can build autonomous agents using LLMs. You will be responsible for creating autonomous agents that can plan, execute, and verify tasks.",
    "employmentType": "Full-time"
}

url = "http://localhost:8000/api/extension/tailor"

print(f"Sending POST to {url}...")
try:
    response = requests.post(url, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()
    print("Success! Backend responded with:")
    print(json.dumps(data, indent=2))
    
    # The backend runs tailoring in the background. We should poll the job status.
    job_id = data.get("id")
    print(f"\nPolling job status for {job_id}...")
    
    for i in range(20):
        time.sleep(2)
        poll_res = requests.get(f"http://localhost:8000/api/tailor/{job_id}")
        poll_data = poll_res.json()
        print(f"Status: {poll_data.get('status')} (Progress: {poll_data.get('progress')}%)")
        if poll_data.get('status') in ['completed', 'failed', 'error']:
            break
            
    print("\nFinal Job Data:")
    print(json.dumps(poll_data, indent=2))
    
    if poll_data.get('status') == 'completed':
        print("\nChecking Applications Dashboard...")
        apps_res = requests.get("http://localhost:8000/api/applications")
        apps = apps_res.json()
        found = False
        for app in apps:
            if app.get("tailoring_job_id") == job_id:
                print(f"FOUND Application in Dashboard: {app['job_title']} at {app['company']}")
                found = True
                break
        if not found:
            print("ERROR: Application not found in dashboard!")
            sys.exit(1)
        else:
            print("PIPELINE TEST PASSED!")
            sys.exit(0)
    else:
        print("ERROR: Tailoring job did not complete successfully.")
        sys.exit(1)
        
except Exception as e:
    print(f"Error occurred: {e}")
    sys.exit(1)

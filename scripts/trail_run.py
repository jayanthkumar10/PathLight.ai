import requests
import time
import json
import os

API_URL = "http://localhost:8000/api"

def run_test():
    print("Starting Trail Run...")
    
    # Check health
    try:
        health = requests.get(f"{API_URL}/health").json()
        print(f"Health Check: {health}")
    except Exception as e:
        print(f"API is not reachable: {e}")
        return

    # Start Tailoring
    payload = {
        "selected_model": "gemini-1.5-flash",
        "target_role": "Python Developer",
        "location": "San Francisco",
        "posted_within": "past_week",
        "requested_jobs": 10
    }
    
    print("\nCreating Tailoring Job...")
    resp = requests.post(f"{API_URL}/tailor", json=payload)
    if resp.status_code != 200:
        print(f"Error creating job: {resp.text}")
        return
        
    job_id = resp.json()["id"]
    print(f"Job Created: {job_id}")
    
    print("\nPolling for status (this may take a few minutes)...")
    completed = False
    
    while not completed:
        try:
            status_resp = requests.get(f"{API_URL}/tailor/{job_id}").json()
            status = status_resp.get("status")
            print(f"Status: {status} | Scanned: {status_resp.get('scanned_jobs', 0)} | Generated: {status_resp.get('generated_resumes', 0)}")
            
            if status in ["Completed", "Failed"]:
                completed = True
            else:
                time.sleep(5)
        except Exception as e:
            print(f"Error polling: {e}")
            time.sleep(5)
            
    print("\nJob Finished.")
    
    print("\nChecking Applications...")
    apps = requests.get(f"{API_URL}/applications").json()
    my_apps = [a for a in apps if a["tailoring_job_id"] == job_id]
    
    for app in my_apps:
        print(f"\n--- Application {app['id']} ---")
        print(f"Company: {app.get('company')}")
        print(f"Title: {app.get('job_title')}")
        print(f"Status: {app.get('application_status')}")
        print(f"Score: {app.get('ats_score')}")
        print(f"Generation Time: {app.get('generation_time')}s")
        missing = app.get('missing_keywords')
        print(f"Feedback/Missing: {str(missing)[:100]}...")
        if app.get("generated_resume_path"):
            print(f"PDF Path: {app.get('generated_resume_path')}")
            
if __name__ == "__main__":
    run_test()

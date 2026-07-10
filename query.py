import sqlite3
conn = sqlite3.connect('pathlight.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("TABLES:", c.fetchall())
c.execute("PRAGMA table_info(applications)")
print("APPLICATION COLUMNS:", [row[1] for row in c.fetchall()])
c.execute("SELECT id, company, job_title, apply_link, application_status, ats_score, generation_time FROM applications ORDER BY rowid DESC LIMIT 10")
rows = c.fetchall()
print(f"\nAPPLICATIONS ({len(rows)} rows):")
for r in rows:
    print(r)
c.execute("SELECT id, status, target_role, scanned_jobs, matched_jobs, generated_resumes FROM tailoring_jobs ORDER BY rowid DESC LIMIT 5")
rows = c.fetchall()
print(f"\nTAILORING_JOBS:")
for r in rows:
    print(r)
conn.close()

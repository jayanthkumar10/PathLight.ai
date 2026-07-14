"""
One-time migration: parse the real uploaded resume and update master_resumes table.
Also adds action_verbs column if missing.
"""
import sqlite3
import os
import sys

# Try pdfplumber first, fall back to pypdf
try:
    import pdfplumber
    PDF_LIB = "pdfplumber"
except ImportError:
    try:
        from pypdf import PdfReader
        PDF_LIB = "pypdf"
    except ImportError:
        print("ERROR: No PDF library available. Install pdfplumber or pypdf.")
        sys.exit(1)

print(f"Using PDF lib: {PDF_LIB}")

REAL_PDF = r"uploads\2933d96c-eee6-477c-95d5-fe02e7e53c8e_jayanth_resume_july2 (1).pdf"
RESUME_ID = r"uploads\resumes\e9acbc9c-c5da-434b-9ac4-4b7e207b1c62.pdf"

if not os.path.exists(REAL_PDF):
    print(f"ERROR: Real PDF not found at {REAL_PDF}")
    sys.exit(1)

print(f"Found real PDF: {REAL_PDF} ({os.path.getsize(REAL_PDF)} bytes)")

# ── Extract text ──────────────────────────────────────────────────────────────
def extract_text(path):
    if PDF_LIB == "pdfplumber":
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    else:
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

text = extract_text(REAL_PDF)
print(f"Extracted {len(text)} characters from PDF")
print("--- FIRST 500 CHARS ---")
print(text[:500])
print("--- END ---")

# ── Simple skill extractor ────────────────────────────────────────────────────
def extract_skills_from_text(text):
    import re
    t = text.lower()
    
    hard_skills_pool = [
        "python", "java", "javascript", "typescript", "sql", "nosql", "mongodb",
        "postgresql", "mysql", "redis", "docker", "kubernetes", "git", "github",
        "fastapi", "flask", "django", "rest api", "graphql", "microservices",
        "aws", "gcp", "azure", "terraform", "ci/cd", "jenkins", "linux",
        "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow", "keras",
        "langchain", "langgraph", "rag", "vector database", "pinecone", "chromadb",
        "openai", "gemini", "llm", "transformer", "bert", "gpt",
        "machine learning", "deep learning", "nlp", "computer vision",
        "data analysis", "data engineering", "spark", "kafka", "airflow",
        "html", "css", "react", "node.js", "express", "next.js"
    ]
    
    soft_skills_pool = [
        "communication", "teamwork", "leadership", "problem-solving", "critical thinking",
        "time management", "adaptability", "collaboration", "agile", "scrum",
        "project management", "analytical", "creativity", "attention to detail"
    ]
    
    action_verbs_pool = [
        "developed", "built", "designed", "implemented", "deployed", "optimized",
        "automated", "integrated", "led", "managed", "collaborated", "created",
        "engineered", "architected", "streamlined", "accelerated", "reduced",
        "increased", "improved", "delivered", "launched", "maintained", "monitored",
        "analyzed", "researched", "trained", "fine-tuned", "evaluated"
    ]
    
    found_hard = [s for s in hard_skills_pool if s in t]
    found_soft = [s for s in soft_skills_pool if s in t]
    found_verbs = [v for v in action_verbs_pool if v in t]
    
    return found_hard, found_soft, found_verbs

hard, soft, verbs = extract_skills_from_text(text)
print(f"\nExtracted: {len(hard)} hard skills, {len(soft)} soft skills, {len(verbs)} action verbs")
print("Hard:", hard[:10])
print("Soft:", soft[:5])
print("Verbs:", verbs[:8])

# ── Update DB ────────────────────────────────────────────────────────────────
conn = sqlite3.connect('pathlight.db')
c = conn.cursor()

# Add action_verbs column if missing
try:
    c.execute("ALTER TABLE master_resumes ADD COLUMN action_verbs TEXT")
    conn.commit()
    print("\nAdded action_verbs column")
except sqlite3.OperationalError:
    print("\naction_verbs column already exists")

# Also copy real PDF to the expected path
import shutil
os.makedirs("uploads/resumes", exist_ok=True)
shutil.copy2(REAL_PDF, RESUME_ID)
print(f"Copied real PDF to {RESUME_ID}")

# Update master_resumes with real data
c.execute("""
    UPDATE master_resumes SET
        original_filename = ?,
        storage_path = ?,
        parsed_text = ?,
        hard_skills = ?,
        soft_skills = ?,
        technical_skills = ?,
        action_verbs = ?,
        parsed_json = ?
    WHERE id = '00d90081-ed54-4d53-b5bd-ffd021209f58'
""", (
    "Jayanth_Resume.pdf",
    RESUME_ID,
    text,
    ",".join(hard),
    ",".join(soft),
    ",".join(hard),  # technical = same as hard for now
    ",".join(verbs),
    '{"years_of_experience": 2, "candidate_name": "Jayanth Kumar Pillajetti", "current_title": "Software Engineer | AI & Data", "contact_info": "pillajettijayanth@gmail.com | +91 91339 85109 | Mumbai, India"}'
))

if c.rowcount == 0:
    print("No existing row to update — inserting new master resume record")
    import uuid, hashlib
    hash_val = hashlib.md5(text.encode()).hexdigest()
    c.execute("""
        INSERT INTO master_resumes 
        (id, original_filename, storage_path, parsed_text, hard_skills, soft_skills, technical_skills, action_verbs, parsed_json, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        "Jayanth_Resume.pdf",
        RESUME_ID,
        text,
        ",".join(hard),
        ",".join(soft),
        ",".join(hard),
        ",".join(verbs),
        '{"years_of_experience": 2, "candidate_name": "Jayanth Kumar Pillajetti", "current_title": "Software Engineer | AI & Data", "contact_info": "pillajettijayanth@gmail.com | +91 91339 85109 | Mumbai, India"}',
        hash_val
    ))

conn.commit()

# Verify
c.execute("SELECT id, original_filename, length(parsed_text), hard_skills, soft_skills, action_verbs FROM master_resumes")
rows = c.fetchall()
print("\n✅ Updated master_resumes:")
for r in rows:
    print(f"  id={r[0][:8]}... | file={r[1]} | text_len={r[2]} | hard_n={len((r[3] or '').split(','))} | verbs_n={len((r[5] or '').split(','))}")

conn.close()
print("\n✅ Migration complete!")

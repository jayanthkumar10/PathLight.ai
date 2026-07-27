# Agent & Pipeline Documentation

The core "magic" of Pathlight.ai lies in its AI pipelines, located within `backend/services/pipeline.py`.

## The Tailoring Pipeline
When a tailoring job is triggered, the background Celery worker initiates the following sequence:

1. **Job Intake**: The system receives either a raw job description (via the extension) or uses Apify to scrape relevant job listings based on the user's target role.
2. **Master Profile Retrieval**: The system fetches the user's current Master Profile from the database.
3. **Keyword Extraction (Intelligence Cache)**: 
   - An LLM prompt is executed to extract hard requirements, soft skills, and years of experience (YOE) from the Job Description.
   - *Optimization*: The results are hashed and stored in `JDIntelligenceCache` to prevent re-running expensive extractions on the same job posting.
4. **Evidence Mapping & Rewriting**:
   - The LLM compares the Master Profile against the extracted JD requirements.
   - It identifies matching skills and rewrites bullet points to emphasize relevant experience using the exact terminology found in the JD (crucial for passing ATS parsers).
5. **Resume Generation**:
   - The rewritten content is merged into a pre-defined HTML template.
   - The HTML is converted to a PDF using a PDF rendering engine (like WeasyPrint).
6. **Scoring**:
   - The final output is analyzed to calculate an `ats_score` and `fit_score`.
7. **Completion**:
   - The database is updated, marking the job as `completed`.

## LLM Routing
The pipeline is agnostic to the underlying LLM provider. Based on user selection or configuration, requests are routed to:
- Google Gemini (`GEMINI_API_KEY`)
- Mistral AI (`MISTRAL_API_KEY`)
- OpenRouter (`OPEN_ROUTER_API_KEY`) 

This ensures high availability and allows users to select models based on cost vs. reasoning capabilities.

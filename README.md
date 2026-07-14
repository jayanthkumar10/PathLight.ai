# Pathlight.ai

**Pathlight.ai** is an AI-powered Job Co-Pilot and ATS-optimized resume tailor. It allows users to automatically generate perfectly tailored resumes targeting specific job descriptions, drastically improving their chances of passing Applicant Tracking Systems (ATS).

## 🚀 Core Features

- **Automated Resume Tailoring**: Leverages Google Gemini and OpenRouter models to rewrite and optimize resumes against specific Job Descriptions.
- **Dynamic Job Scraping**: Uses Apify to scrape live job postings directly from job boards via URL.
- **Intelligent PDF Generation**: Converts HTML resumes into beautifully formatted, ATS-friendly PDFs using WeasyPrint.
- **LLM Observability**: Integrated with Langfuse (via OpenTelemetry) to monitor token usage, API costs, LLM latency, and generation quality in real-time.
- **Background Processing**: Heavy AI generation tasks are offloaded to Celery background workers to ensure the web application remains blazing fast and responsive.

---

## 🛠️ Complete Tech Stack

Pathlight.ai utilizes a modern, containerized architecture separating a lightweight frontend from a robust, asynchronous Python backend.

### Frontend (Client-Side)
- **HTML5 / CSS3 / JavaScript (ES6+)**: A dependency-free, vanilla frontend architecture designed for maximum performance without the overhead of heavy frameworks like React or Vue.
- **Client-Side Routing**: Custom vanilla JavaScript implementations to handle dynamic data fetching and DOM updates seamlessly.

### Backend (Server-Side)
- **Python (3.11+)**: The core programming language.
- **FastAPI**: A high-performance, asynchronous web framework for building the REST APIs.
- **Uvicorn**: The ASGI web server used to serve the FastAPI application.
- **Pydantic**: Used for strict data validation, serialization, and settings/environment management.

### Database & Caching
- **PostgreSQL (v15)**: The primary relational database used to store users, tailored resumes, and job application tracking data.
- **SQLAlchemy**: The Object-Relational Mapper (ORM) used to interact with PostgreSQL using Python objects.
- **Psycopg2**: The PostgreSQL database adapter for Python.
- **Redis (v7)**: An in-memory data store acting as the message broker for background task queues.

### Background Processing
- **Celery**: A distributed task queue system. All LLM calls (which take several seconds) are offloaded to Celery workers so the main API does not block or timeout.

### AI / Large Language Models
- **Google Gemini API**: Default models (e.g., `gemini-1.5-flash`) used for rapid, high-quality resume generation.
- **OpenRouter API**: Acts as a robust fallback mechanism (using models like `meta-llama/llama-3.3-70b-instruct:free`) if Gemini rate-limits or fails.
- **Langfuse**: Provides full observability for the LLMs, tracking traces, token costs, prompt inputs/outputs, and latency.

### Document Processing & NLP
- **WeasyPrint**: Converts raw HTML resumes into pixel-perfect PDF documents.
- **pdfplumber & pypdf**: Extracts and parses text from user-uploaded PDF resumes.
- **python-docx**: Parses Microsoft Word (`.docx`) documents.
- **spaCy & rapidfuzz**: Used for Natural Language Processing and fuzzy string matching (e.g., matching user skills to JD skills).

### Integrations & Security
- **Apify Client**: Integrates with Apify actors to scrape job boards securely.
- **PyJWT, passlib, bcrypt, python-jose**: The security stack used to hash user passwords and issue JSON Web Tokens (JWT) for secure authentication.

### Infrastructure & Deployment
- **Docker & Docker Compose**: The entire application is containerized. A single `docker-compose.yml` orchestrates the API, Celery Worker, PostgreSQL, and Redis containers in complete isolation.

---

## 🏗️ Architecture Overview

1. **Client Request**: The user submits a job description (via text or URL) and requests a tailored resume from the frontend.
2. **API Layer**: FastAPI receives the request, validates the payload using Pydantic, and saves a "Pending" job state in PostgreSQL.
3. **Message Queue**: FastAPI pushes the tailoring task onto the Redis message queue.
4. **Background Worker**: A Celery Worker picks up the task from Redis and begins processing.
5. **AI Processing**: The Celery worker parses the user's base resume, constructs a highly-optimized prompt, and streams it to Google Gemini (or OpenRouter).
6. **Observability**: As the AI generates the text, Langfuse intercepts the request to record token counts, generation time, and costs.
7. **Completion & PDF**: The worker saves the newly generated HTML resume to the database, triggers WeasyPrint to generate a PDF, and updates the job status to "Completed".
8. **Client Update**: The frontend (which has been polling or waiting) receives the "Completed" status and displays the stunning new resume to the user.

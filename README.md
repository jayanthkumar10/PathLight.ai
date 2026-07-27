<div align="center">
  <h1>Pathlight.ai 🚀</h1>
  <p><strong>Full ATS-Optimized Resume Tailoring Platform</strong></p>
</div>

<br>

## What is Pathlight?
Pathlight is an intelligent platform designed to automatically tailor resumes to specific job descriptions using advanced AI models. It ensures that your resume passes through Applicant Tracking Systems (ATS) by intelligently matching your skills, rewriting your bullet points, and highlighting your most relevant experiences for the role you're applying for.

## Problem Statement
Job seekers often struggle to get their resumes past automated Applicant Tracking Systems (ATS), resulting in qualified candidates being rejected before a human even reviews their application. Manually tailoring a resume for every single job application is incredibly time-consuming, tedious, and often imprecise. Pathlight automates this workflow, saving hours of work while drastically improving interview callback rates.

## Architecture Diagram
```mermaid
graph TD
    A[Frontend UI / Chrome Ext] -->|REST API| B[FastAPI Backend]
    B -->|Database Operations| C[(PostgreSQL)]
    B -->|Task Queue| D[Celery Workers]
    D -->|Cache & Message Broker| E[(Redis)]
    D -->|AI Processing| F[LLM APIs]
    F -.->|Gemini / Mistral / OpenRouter| G[AI Engine]
```

## Features
- ✨ **AI-Powered Resume Tailoring:** Leverages Gemini, Mistral, and other state-of-the-art LLMs to rewrite and optimize resume content perfectly.
- 🧩 **Chrome Extension Integration:** Seamlessly start tailoring jobs directly from job boards like LinkedIn with a single click.
- 📊 **ATS Scoring:** Automatically calculates ATS fit and match scores based on the provided job description.
- 📄 **PDF Generation:** Exports the fully tailored resume to a clean, highly ATS-readable PDF format.
- 📈 **Application Tracking:** Built-in dashboard to manage all your tailored resumes and track your job application statuses.

## Installation
Clone the repository to your local machine:
```bash
git clone https://github.com/jayanthkumar10/PathLight.ai.git
cd PathLight.ai
```

## Configuration
1. Copy the example environment file to `.env`:
```bash
cp .env.example .env
```
2. Populate the required API keys (Gemini, OpenRouter, Apify, etc.) inside your new `.env` file.

## Run Backend
The easiest way to run the entire backend stack (FastAPI, PostgreSQL, Redis, Celery) is by using Docker Compose:

```bash
docker-compose up -d --build
```
Alternatively, you can use the provided startup scripts:
```bash
./start.bat  # On Windows
./start.sh   # On Linux/macOS
```
The API will be available at `http://localhost:8000`. Interactive API documentation is automatically generated and available at `http://localhost:8000/docs`.

## Run Frontend
The frontend consists of static files that are served directly by the FastAPI backend from the `public/` directory. Once the backend is running, simply navigate to `http://localhost:8000` in your web browser to use the application.

## Environment Variables
Here are the key environment variables used in Pathlight:
- `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql://postgres:postgres@postgres:5432/pathlight`)
- `REDIS_URL`: Connection string for Redis broker (e.g., `redis://redis:6379/0`)
- `GEMINI_API_KEY`: API key for Google Gemini models
- `APIFY_API_TOKEN`: API token for Apify integration (used for scraping)
- `OPEN_ROUTER_API_KEY`: API key for accessing OpenRouter LLMs
- `MISTRAL_API_KEY`: API key for Mistral AI
- `JWT_SECRET`: Secret key for JWT authentication sessions
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: OAuth credentials for Google Sign-In integration

## Screenshots
*(Add screenshots of the Pathlight dashboard and generated resumes here)*

## Roadmap
- [ ] Add support for more LLM providers and local models.
- [ ] Improve the ATS scoring and keyword matching algorithm.
- [ ] Add multi-language resume support.
- [ ] Enhance Chrome extension with automatic application form filling.

## Contributing
Contributions are always welcome! Please feel free to open an issue or submit a pull request with your proposed changes.

## License
This project is licensed under the MIT License.

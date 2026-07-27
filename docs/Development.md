# Development Setup

This guide covers setting up Pathlight.ai for local development.

## Prerequisites
- Python 3.11+
- Node.js (for potential future frontend tooling)
- Docker Desktop
- Git

## Environment Setup
1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your API keys (Gemini, OpenRouter, etc.).
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running Locally (Docker - Recommended)
The simplest way to run the full stack locally is with Docker:
```bash
docker-compose up -d --build
```
This spins up the database, redis, celery, and the API. The API will be hot-reloaded automatically.

## Running Locally (Native/Scripts)
If you prefer running services natively, ensure you have PostgreSQL and Redis running locally. Then use the provided helper scripts:
```bash
# On Windows
./start.bat

# On Linux/macOS
./start.sh
```

## IDE Configuration
- **VS Code**: We recommend installing the Python, Pylance, and Docker extensions.
- **Pre-commit Hooks**: We recommend running `black` and `flake8` locally before submitting pull requests.

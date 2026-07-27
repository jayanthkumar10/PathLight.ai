# Backend Documentation

The backend of Pathlight.ai is powered by [FastAPI](https://fastapi.tiangolo.com/), providing a robust, async-ready web framework.

## Directory Structure
- `backend/main.py`: The entry point for the application. Mounts routers and static files.
- `backend/routers/`: Contains isolated route definitions (e.g., `auth.py`, `dashboard.py`, `resume.py`, `studio.py`).
- `backend/models/`: SQLAlchemy ORM definitions mapping to PostgreSQL tables.
- `backend/schemas/`: Pydantic models for request validation and response serialization.
- `backend/services/`: Core business logic, including the AI pipeline (`pipeline.py`).
- `backend/repositories/`: Data access layer abstracting direct database calls.
- `backend/core/`: Configuration logic (`config.py`) that loads from `.env`.

## Key Technologies
- **FastAPI**: API framework.
- **Uvicorn**: ASGI server.
- **SQLAlchemy**: Database ORM.
- **Alembic**: Database migrations (if configured in future).
- **Celery**: Background task processing.
- **PyJWT & Passlib**: Authentication and password hashing.
- **WeasyPrint / PyPDF**: PDF generation and manipulation.

## Bootstrapping
When `docker-compose up` is executed, the `api` container runs `uvicorn backend.main:app --host 0.0.0.0 --port 8000`. This starts the web server. Simultaneously, the `celery_worker` container boots up and listens to the Redis queue for incoming LLM generation requests.

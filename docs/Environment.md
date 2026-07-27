# Environment Variables

Pathlight.ai requires several environment variables to function correctly. These should be defined in a `.env` file at the root of the project. 

> **Security Warning**: Never commit your `.env` file to version control.

## External APIs (LLM & Scraping)
- `GEMINI_API_KEY`: Required for Google's Gemini models (default engine).
- `OPEN_ROUTER_API_KEY`: Required if using OpenRouter models.
- `MISTRAL_API_KEY`: Required if using Mistral AI models.
- `APIFY_API_TOKEN`: Required for scraping LinkedIn job descriptions via Apify.

## Application Configuration
- `ENVIRONMENT`: Set to `development` or `production`.
- `LOG_LEVEL`: Standard Python logging levels (`INFO`, `DEBUG`, `WARNING`, `ERROR`).

## Database & Cache
- `DATABASE_URL`: Connection string for PostgreSQL.
  - *Example*: `postgresql://postgres:postgres@localhost:5432/pathlight`
- `REDIS_URL`: Connection string for Redis.
  - *Example*: `redis://localhost:6379/0`

## Authentication (Google OAuth)
- `GOOGLE_CLIENT_ID`: OAuth client ID obtained from Google Cloud Console.
- `GOOGLE_CLIENT_SECRET`: OAuth client secret.
- `GOOGLE_REDIRECT_URI`: The callback URI registered in Google Cloud.
- `JWT_SECRET`: A long, random string used to sign JWT session tokens.

## Observability (Optional)
- `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL`: Configuration for Langfuse LLM observability and tracing.

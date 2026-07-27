# Troubleshooting

Common issues and their resolutions when running Pathlight.ai.

## 1. Localhost 8000 is unreachable
**Symptoms**: You ran `docker-compose up` but `http://localhost:8000` times out.
**Cause**: The Docker daemon (specifically WSL2 integration on Windows) may have deadlocked, or port 8000 is occupied by another process.
**Resolution**: 
- Restart Docker Desktop entirely.
- Run `docker ps` to ensure the `pathlight-api-1` container is marked as `Up`.
- Check logs: `docker logs pathlight-api-1`

## 2. Celery Jobs stuck in "Pending"
**Symptoms**: You clicked "Start Tailoring" but the status never changes.
**Cause**: The Celery worker is either not running or cannot connect to Redis.
**Resolution**:
- Check the worker logs: `docker logs pathlight-celery_worker-1`.
- Ensure Redis is running and accessible at the `REDIS_URL` specified in your `.env`.

## 3. PDF Generation Errors
**Symptoms**: Application status says completed, but the PDF download fails.
**Cause**: Missing system dependencies for PDF generation (like Pango, cairo, or GTK).
**Resolution**: 
- If running natively (not Docker), ensure you have installed the C-level libraries required by WeasyPrint. 
- If running in Docker, ensure the Dockerfile includes `apt-get install -y pango1.0-tools` (or equivalent).

## 4. API Keys Failing
**Symptoms**: Job status goes to `failed` immediately.
**Cause**: Invalid or missing LLM API keys.
**Resolution**: Check your `.env` file to ensure `GEMINI_API_KEY` (or the respective provider) is correct and has available quota. Check the `celery.log` for the exact API error response.

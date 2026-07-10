@echo off
echo Starting Pathlight Stabilized Architecture...

echo.
echo Bringing up Docker Compose Stack (Unified API, DB, Redis)...
docker-compose up -d --build

echo.
echo ===================================================
echo Services have been launched!
echo - Web Application: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo ===================================================
echo To view Docker logs, run: docker-compose logs -f

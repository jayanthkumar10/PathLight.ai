#!/bin/bash
echo "Starting Pathlight Stabilized Architecture..."

echo ""
echo "Bringing up Docker Compose Stack..."
echo "This will start:"
echo "- FastAPI Backend (Port 8000)"
echo "- Celery Worker"
echo "- PostgreSQL Database (Port 5434)"
echo "- Redis (Port 6380)"
echo ""

docker-compose up -d --build

echo ""
echo "==================================================="
echo "Services have been launched in the background!"
echo "- Web Application: http://localhost:8000"
echo "- Swagger API Docs: http://localhost:8000/docs"
echo "==================================================="
echo "To view logs, run: docker-compose logs -f"

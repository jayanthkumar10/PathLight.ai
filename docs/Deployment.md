# Deployment

Pathlight.ai is containerized, making deployment straightforward.

## Production Deployment
The recommended deployment path is using Docker Compose.

1. Clone the repository on your production server.
2. Configure `.env` with production keys and secrets.
3. Start the stack:
   ```bash
   docker-compose up -d --build
   ```

### Docker Compose Architecture
The `docker-compose.yml` defines the following services:
- **`api`**: The FastAPI application serving requests on port 8000.
- **`postgres`**: The PostgreSQL database (port 5432).
- **`redis`**: The Redis message broker and cache (port 6379).
- **`celery_worker`**: The Celery process consuming LLM jobs from Redis.

### Reverse Proxy Configuration
In a production environment, you should place a reverse proxy (like Nginx or Caddy) in front of the `api` service to handle SSL/TLS termination and route port 80/443 to port 8000.

### Scaling
If the volume of tailoring jobs increases, you can scale the Celery workers independently of the API:
```bash
docker-compose up -d --scale celery_worker=3
```

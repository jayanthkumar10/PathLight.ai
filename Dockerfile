FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for postgres and building extensions
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

    # Copy backend requirements and install
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    RUN python -m spacy download en_core_web_sm

# Copy the entire project context
COPY . .

# Expose port for FastAPI
EXPOSE 8000

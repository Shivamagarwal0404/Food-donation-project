# =============================================================================
# FoodShare — Backend Dockerfile
# Python 3.12 / Django / Gunicorn
# =============================================================================

FROM python:3.12-slim

# Prevent .pyc files, unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies (Pillow, psycopg2 build deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Create directories that Django needs
RUN mkdir -p /app/media /app/staticfiles

# Non-root user for security
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Default: Gunicorn production server. Overridden with runserver in dev docker-compose.yml.
CMD ["gunicorn", "config.wsgi:application", "-c", "gunicorn.conf.py"]

# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-copy requirements for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# Copy source
COPY . /app

# Create data directories
RUN mkdir -p /data/chroma /db

# Expose FastAPI default port
EXPOSE 8000

# Healthcheck: ping root endpoint
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8000/ || exit 1

# Default command uses uvicorn to serve FastAPI app
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]



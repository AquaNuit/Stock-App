# Optimized Dockerfile for Hugging Face Spaces (free tier, ~1 GB RAM)
# SDK: docker | App port: 7860
# Build context should be repo root.

FROM python:3.11-slim

# Prevent interactive prompts during apt
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HF_HOME=/tmp/huggingface-cache
ENV TOKENIZERS_PARALLELISM=false
ENV PIP_NO_CACHE_DIR=1
ENV ENV=prod
ENV DATABASE_URL=sqlite:///./stocksense.db
ENV SCHEDULER_ENABLED=true
ENV SEED_FALLBACK=true
ENV CORS_ORIGINS=https://*.netlify.app,http://localhost:5173
ENV RATE_LIMIT_PER_MINUTE=120
ENV MAX_CONCURRENT_TRAINS=5
ENV ML_MAX_TRAINING_ROWS=750
ENV ML_DEFAULT_MODELS=linear,random_forest
ENV LOG_LEVEL=INFO

# Install minimal system dependencies (git for any clone, build tools for numpy/scipy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend /app/backend
COPY .env.example /app/.env

# Create a lightweight .env that overrides with HF-safe defaults
RUN echo 'ENV=prod' >> /app/.env \
    && echo 'DATABASE_URL=sqlite:///./stocksense.db' >> /app/.env \
    && echo 'SCHEDULER_ENABLED=true' >> /app/.env \
    && echo 'SEED_FALLBACK=true' >> /app/.env \
    && echo 'CORS_ORIGINS=https://*.netlify.app,http://localhost:5173' >> /app/.env \
    && echo 'MAX_CONCURRENT_TRAINS=5' >> /app/.env \
    && echo 'ML_MAX_TRAINING_ROWS=750' >> /app/.env \
    && echo 'ML_DEFAULT_MODELS=linear,random_forest' >> /app/.env \
    && echo 'LOG_LEVEL=INFO' >> /app/.env \
    && echo 'RATE_LIMIT_PER_MINUTE=120' >> /app/.env

# Copy root README.md required by HF Spaces (use space-specific README)
COPY README_SPACE.md /app/README.md

# Make sure SQLite DB is writable (persisted in container layer)
RUN touch /app/stocksense.db && chmod 666 /app/stocksense.db || true

# Expose port expected by HF Spaces (Docker SDK)
EXPOSE 7860

# Health check endpoint (fast, low memory)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ping || exit 1

# Run with single uvicorn worker (low memory footprint)
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1", "--timeout-keep-alive", "5"]

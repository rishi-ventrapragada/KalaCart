# ==============================================================================
# Multi-Stage Production Dockerfile for KalaCart FastAPI
# ==============================================================================

# Stage 1: Build & wheels
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final minimal runtime
FROM python:3.11-slim AS runner

# Create non-root system user for security
RUN groupadd -g 1001 kalacart && \
    useradd -u 1001 -g kalacart -m -s /bin/bash kalacart

WORKDIR /app

# Install runtime shared libraries for image processing & curl health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy python packages from builder
COPY --from=builder --chown=kalacart:kalacart /root/.local /home/kalacart/.local

ENV PATH=/home/kalacart/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Copy application source
COPY --chown=kalacart:kalacart . .

USER kalacart

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]

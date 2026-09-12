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

# Render injects PORT (its documented default is 10000); this ENV is the
# fallback so `docker run` works locally with no PORT set.
ENV PORT=10000

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# -w 1, not 4: Render's free instance is 0.1 CPU / 512 MB. The app plus OpenCV
# measures ~107 MB resident for a single worker, so four would not fit, and four
# processes on a tenth of a CPU would contend rather than parallelise.
# It is also more correct -- core/rate_limit.py keeps its counters in process
# memory, so multiple workers would each enforce a separate, wrong quota.
# Shell form so ${PORT} is expanded by the shell at runtime.
CMD gunicorn app.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT} --access-logfile - --error-logfile -

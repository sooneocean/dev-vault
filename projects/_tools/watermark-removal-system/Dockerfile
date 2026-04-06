# Multi-stage Docker build for watermark removal system
# Optimizes image size and build time

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Build wheels for faster installation in final stage
RUN pip install --user --no-cache-dir --wheel --no-deps -r requirements.txt && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .

RUN pip install --no-cache /wheels/* && \
    rm -rf /wheels

# Copy application code
COPY . .

# Create directories for inputs/outputs
RUN mkdir -p /data/input /data/output /data/checkpoints /data/config

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8188/api/status || exit 1

# Default command
ENTRYPOINT ["python", "scripts/run_pipeline.py"]

# Default args (can be overridden)
CMD ["--help"]

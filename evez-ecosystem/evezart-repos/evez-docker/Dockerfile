# EVEZ-OS Unified Docker Image
# All 17 services in one container, selectable via CMD
# Built for ARM64 (Oracle) and AMD64 (Vultr)

FROM python:3.12-slim AS base

# Pin all deps, combine layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg espeak-ng curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -r evez && useradd -r -g evez -d /home/evez -s /sbin/nologin evez

WORKDIR /opt/evez

# Copy requirements first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all service code
COPY services/ ./services/
COPY media/ ./media/
COPY scripts/ ./scripts/

# Non-root per skill
USER evez

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Default: ClawBreak
ENV PORT=8080
CMD ["python", "-m", "uvicorn", "services.clawbreak:app", "--host", "0.0.0.0", "--port", "8080"]

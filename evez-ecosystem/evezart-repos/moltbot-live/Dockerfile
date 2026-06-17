FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    ffmpeg \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    fonts-dejavu-core \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1
ENV SDL_VIDEODRIVER=x11
ENV STREAM_DISPLAY=:99

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD pgrep -f ffmpeg > /dev/null && pgrep -f dashboard.py > /dev/null

# Run
CMD ["python", "stream.py"]

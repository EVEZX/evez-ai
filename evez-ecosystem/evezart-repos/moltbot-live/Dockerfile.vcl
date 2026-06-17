FROM python:3.11-slim

# System deps: Xvfb, FFmpeg, Chromium, fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    ffmpeg \
    chromium \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-color-emoji \
    x11-utils \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY visualizer/ /app/visualizer/
COPY stream_vcl.py /app/stream_vcl.py
COPY run_forever.sh /app/run_forever.sh
RUN chmod +x /app/run_forever.sh

ENV PYTHONUNBUFFERED=1
ENV STREAM_DISPLAY=:99
ENV STREAM_WIDTH=1280
ENV STREAM_HEIGHT=720
ENV FPS=30
ENV BITRATE=2500k
ENV VCL_HTML=/app/visualizer/index.html
ENV HEALTH_PORT=8080
ENV MOLTBOT_CMD="python stream_vcl.py"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -sf http://localhost:8080/ || exit 1

CMD ["bash", "run_forever.sh"]

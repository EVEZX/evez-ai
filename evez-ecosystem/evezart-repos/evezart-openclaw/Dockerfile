FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl ca-certificates sqlite3 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY evez_gateway.py .
COPY openclaw.json .

RUN mkdir -p /data static

# HF Spaces uses port 7860
ENV PORT=7860
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "evez_gateway:app", "--host", "0.0.0.0", "--port", "7860", \
     "--ws-ping-interval", "30", "--ws-ping-timeout", "10"]

FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Copy workspace files
COPY . /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for evez-os
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install -r /app/projects/evez-os/requirements.txt

# Expose default port (if any)
EXPOSE 8000

# Set entrypoint to run evez-os server (example)
CMD ["/app/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

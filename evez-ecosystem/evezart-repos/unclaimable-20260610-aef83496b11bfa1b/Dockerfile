# Use a slim Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg for audio handling if needed)
RUN apt-get update && apt-get install -y --no-install-recommends 
    ffmpeg 
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Command to run the server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

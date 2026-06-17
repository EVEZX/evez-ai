FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || pip install fastapi uvicorn httpx groq stripe python-multipart
COPY . .
EXPOSE 8080
CMD ["python3", "server.py"]

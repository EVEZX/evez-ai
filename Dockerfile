FROM python:3.12-slim
WORKDIR /app
COPY provider/requirements.txt provider/ 2>/dev/null || true
RUN pip install --no-cache-dir aiohttp
COPY . .
EXPOSE 9100 9800 9700
CMD ["python3", "provider/gateway-v2.py"]

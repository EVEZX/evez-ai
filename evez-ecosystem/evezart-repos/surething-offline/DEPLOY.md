# SureThing Offline — Deployment Guide

## Option 1: Local (fastest)

```bash
git clone https://github.com/EvezArt/surething-offline
cd surething-offline
bash bootstrap.sh
```

## Option 2: Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data/chroma data/drafts
EXPOSE 8420
CMD ["python", "run.py"]
```

```bash
docker build -t surething-offline .
docker run -p 8420:8420 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 -v $(pwd)/data:/app/data surething-offline
```

## Option 3: Docker Compose

```yaml
version: "3.9"
services:
  ollama:
    image: ollama/ollama
    volumes: [ollama_data:/root/.ollama]
    ports: ["11434:11434"]
    command: serve
  surething:
    build: .
    ports: ["8420:8420"]
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      OLLAMA_MODEL: mistral
    volumes: ["./data:/app/data"]
    depends_on: [ollama]
volumes:
  ollama_data:
```

## Option 4: Raspberry Pi / systemd

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull phi3
git clone https://github.com/EvezArt/surething-offline && cd surething-offline
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env  # edit to set model=phi3

sudo tee /etc/systemd/system/surething.service <<EOF
[Unit]
Description=SureThing Offline
After=network.target
[Service]
User=pi
WorkingDirectory=/home/pi/surething-offline
ExecStart=/home/pi/surething-offline/.venv/bin/python run.py
Restart=always
EnvironmentFile=/home/pi/surething-offline/.env
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable surething && sudo systemctl start surething
```

## Model Recommendations

| Hardware | Model | RAM |
|----------|-------|-----|
| Mac M1+ | mistral, llama3 | 8GB+ |
| GPU workstation | llama3:8b | 8GB VRAM |
| Pi / low-power | phi3:mini | 4GB |

```bash
ollama pull mistral   # default
ollama pull llama3    # stronger
ollama pull phi3:mini # lightest
```

## What No Paywall Means

| Cloud | Offline |
|-------|---------|
| Monthly sub | $0 |
| Cloud APIs | Local Ollama |
| Cloud data | ./data/ |
| Feature gates | None |
| Account | Not required |

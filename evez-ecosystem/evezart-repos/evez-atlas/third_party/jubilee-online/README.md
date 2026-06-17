# Jubilee Forgiveness Service

This directory contains the Jubilee forgiveness service, a FastAPI-based microservice that provides debt forgiveness rituals with event logging and IBM Quantum integration.

## Overview

The Jubilee service is a stub implementation designed to work with the OpenClaw swarm workflow. It provides:

- RESTful API endpoints for forgiveness operations
- Event logging to `data/events.jsonl`
- Health check endpoint
- Docker containerization
- IBM Quantum mode support

## Quick Start

### Using Docker Compose (Recommended)

```bash
cd third_party/jubilee-online
docker compose up -d --build
```

### Manual Setup

```bash
cd third_party/jubilee-online
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/healthz
```

### Forgiveness Ritual
```bash
curl -X POST http://localhost:8000/forgive \
  -H 'Content-Type: application/json' \
  -d '{"account_id": "SWARM1", "amount": 100.0, "reason": "test"}'
```

### View Events
```bash
curl http://localhost:8000/events?limit=10
```

### Service Info
```bash
curl http://localhost:8000/
```

## Configuration

### Environment Variables

- `JUBILEE_MODE` - Service mode (default: `qsvc-ibm`)
- `JUBILEE_TOUCH_ID` - Touch identifier (default: `8e5526c72cebad3c09e4158399eaab06`)
- `JUBILEE_HMAC_SECRET` - HMAC secret for authentication
- `QISKIT_IBM_TOKEN` - IBM Quantum authentication token (optional)

### Example Configuration

```bash
export JUBILEE_MODE=qsvc-ibm
export JUBILEE_TOUCH_ID=8e5526c72cebad3c09e4158399eaab06
export JUBILEE_HMAC_SECRET=$(openssl rand -hex 32)
export QISKIT_IBM_TOKEN=your_token_here
```

### Example Forgiveness

```bash
curl -X POST http://localhost:8000/forgive \
  -H 'Content-Type: application/json' \
  -d '{"account_id":"SWARM1", "amount":100.0, "reason":"test"}'
```

## Docker Compose

The service includes a complete Docker Compose configuration with:

- Automatic container restart
- Health checks
- Volume mounts for data persistence
- Network isolation
- Port mapping (8000:8000)

## File Structure

```
jubilee-online/
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Container build instructions
├── main.py              # FastAPI service implementation
├── requirements.txt     # Python dependencies
├── data/                # Event logs (created at runtime)
└── logs/                # Service logs (created at runtime)
```

## Event Logging

All forgiveness events are logged to `data/events.jsonl` in JSON Lines format:

```json
{
  "event_type": "forgiveness",
  "account_id": "SWARM1",
  "amount": 100.0,
  "reason": "test",
  "status": "forgiven",
  "timestamp": "2026-02-01T08:00:00.000000",
  "touch_id": "8e5526c72cebad3c09e4158399eaab06"
}
```

## Integration

The Jubilee service integrates with:

1. **OpenClaw Swarm** - Provides forgiveness skills to autonomous agents
2. **Skills/Jubilee.py** - Python client library for service interaction
3. **IBM Quantum** - Optional quantum simulation backend
4. **Moltbook** - AI social network integration (via client)

## Development

### Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py  # or: uvicorn main:app --reload

# Test endpoints
curl http://localhost:8000/healthz
curl -X POST http://localhost:8000/forgive -H 'Content-Type: application/json' -d '{"account_id":"TEST"}'
```

### Building Container

```bash
docker build -t jubilee-service .
docker run -p 8000:8000 -e JUBILEE_MODE=qsvc-ibm jubilee-service
```

## Troubleshooting

### Service Won't Start

1. Check if port 8000 is in use: `lsof -i :8000`
2. Verify Docker is running: `docker ps`
3. Check logs: `docker compose logs -f`

### No Events Being Logged

1. Verify data directory exists and is writable
2. Check volume mounts in docker-compose.yml
3. Review service logs for errors

### Connection Refused

1. Ensure service is running: `curl http://localhost:8000/healthz`
2. Check firewall settings
3. Verify port mapping: `docker ps`

## Security Notes

- Use HMAC authentication in production
- Keep `JUBILEE_HMAC_SECRET` secure
- Do not commit secrets to version control
- Use HTTPS in production deployments
- Implement rate limiting for public endpoints

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [OpenClaw Swarm Setup](../../docs/swarm-setup.md)
- [Main Evez666 Repository](../../README.md)

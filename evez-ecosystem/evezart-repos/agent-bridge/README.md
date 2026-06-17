# EVEZ Agent Bridge

Inter-agent coordination infrastructure for the dual-agent EVEZ stack.

## Services

| Service | Port | Description |
|---------|------|-------------|
| Health Monitor | 9000 | Agent heartbeat tracking |
| Coordination API | 9001 | Shared task board + message queue |
| NATS Bridge | — | Pub/sub messaging via NATS |

## Health Monitor

```bash
curl http://45.63.70.174:9000  # GET agent status
curl -X POST http://45.63.70.174:9000 -d '{"agent":"azra","host":"...","status":"alive"}'  # POST heartbeat
```

## Coordination API

```bash
curl http://45.63.70.174:9001/tasks          # List tasks
curl http://45.63.70.174:9001/messages        # List messages
curl -X POST http://45.63.70.174:9001/tasks -d '{"title":"...","assigned_to":"claw"}'  # Create task
curl -X POST http://45.63.70.174:9001/messages -d '{"from":"azra","to":"claw","body":"..."}'  # Send message
```

## NATS Bridge

Publishes to `evez.agents.*` subjects on `nats://45.63.66.247:4222`.

## Agents

- **Claw 🦀** — Primary agent on 45.63.66.247
- **AZRA 🔥** — Partner agent on 45.63.70.174

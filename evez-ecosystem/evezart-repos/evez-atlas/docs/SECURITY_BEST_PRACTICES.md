# Security Best Practices Guide

## Overview

This guide provides best practices for deploying and operating the Evez666 autonomous agent system securely, with a focus on the production mode security controls for debug routes and agent handoff behavior.

## Quick Start: Production Deployment

For a secure production deployment, configure the following environment variables:

```bash
# Required for production
PRODUCTION_MODE=true
SECRET_KEY=your-strong-random-secret-here

# Recommended security defaults
DEBUG=false
ALLOW_AGENT_HANDOFF=false
ALLOW_SOURCE_CITATION=false
ENABLE_EASTER_EGGS=false
```

## Environment Variables

### Core Security Settings

#### `PRODUCTION_MODE`
- **Purpose**: Enable production security mode
- **Values**: `true` | `false`
- **Default**: `false`
- **Effect**: When `true`, blocks debug endpoints and restricts agent behaviors
- **Recommendation**: **Always set to `true` in production**

#### `DEBUG`
- **Purpose**: Override production restrictions for troubleshooting
- **Values**: `true` | `false`
- **Default**: `false`
- **Effect**: Allows debug routes even when `PRODUCTION_MODE=true`
- **Recommendation**: **Only enable temporarily for emergency troubleshooting**
- **Warning**: ⚠️ Exposes sensitive system information

#### `SECRET_KEY`
- **Purpose**: HMAC signature secret for API responses
- **Format**: Long random string (32+ characters)
- **Recommendation**: 
  - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
  - Rotate periodically (every 90 days minimum)
  - Never commit to version control

### Agent Behavior Controls

#### `ALLOW_AGENT_HANDOFF`
- **Purpose**: Allow "handoff to human" requests
- **Values**: `true` | `false`
- **Default**: `false` (blocked in production)
- **Trigger patterns**: 
  - "handoff to human"
  - "transfer to human"
  - "escalate to human"
- **Use cases**: Enable if your deployment includes human support escalation
- **Recommendation**: Only enable if required by your business logic

#### `ALLOW_SOURCE_CITATION`
- **Purpose**: Allow "show sources" requests
- **Values**: `true` | `false`
- **Default**: `false` (blocked in production)
- **Trigger patterns**:
  - "show sources"
  - "cite sources"
  - "list sources"
- **Use cases**: Enable for transparency/compliance requirements
- **Recommendation**: Enable if regulatory compliance requires source attribution

#### `ENABLE_EASTER_EGGS`
- **Purpose**: Enable UI-only Easter eggs (animations, console messages)
- **Values**: `true` | `false`
- **Default**: `false` (disabled in production)
- **Effect**: Enables hidden commands and console messages
- **Recommendation**: Keep disabled in production for professional appearance

## Protected Debug Routes

The following routes are **automatically blocked** when `PRODUCTION_MODE=true`:

| Route | Purpose | Risk Level |
|-------|---------|-----------|
| `GET /navigation-ui` | Quantum navigation visualization | HIGH |
| `GET /navigation-ui/data` | Raw navigation state JSON | HIGH |
| `GET /swarm-status` | Real-time swarm operational data | CRITICAL |
| `GET /security-info` | Security configuration details | CRITICAL |

### Why These Routes Are Blocked

- **Information Disclosure**: Expose internal system architecture
- **Performance Metrics**: Reveal operational capacity and bottlenecks
- **State Information**: Show active entities and their configurations
- **Security Posture**: Disclose which protections are active

## Agent Behavior Threat Model

### Handoff to Human

**Attack Vector**: Malicious input attempts to trigger human escalation to:
- Waste human operator time
- Gather information from human responses
- Test system boundaries

**Mitigation**: Blocked by default in production

**When to Enable**: 
- Customer support workflows require escalation
- Human-in-the-loop validation is needed
- Compliance mandates human oversight

### Source Citation

**Attack Vector**: Repeated source requests to:
- Map training data
- Discover information leakage
- Enumerate data sources

**Mitigation**: Blocked by default in production

**When to Enable**:
- Legal/regulatory requirements for transparency
- Academic or research applications
- Explicit user agreement includes source attribution

### System Info Reveal

**Attack Vector**: Requests for system information to:
- Discover software versions
- Identify vulnerabilities
- Map infrastructure

**Mitigation**: **Always blocked in production** (cannot be overridden)

**Developer Access**: Use `DEBUG=true` temporarily and disable immediately after

### Workflow Triggers

**Attack Vector**: Attempts to execute arbitrary workflows to:
- Trigger resource-intensive operations
- Execute privileged operations
- Chain exploits

**Mitigation**: Blocked by default, controlled by `ALLOW_AGENT_HANDOFF`

## Monitoring and Auditing

### Audit Log Review

All API requests are logged to `src/memory/audit.jsonl`:

```bash
# Review recent activity
tail -100 src/memory/audit.jsonl | jq

# Check for blocked behaviors
grep -i "403" src/memory/audit.jsonl | jq

# Monitor specific endpoints
grep "/swarm-status" src/memory/audit.jsonl | jq
```

### Event Log Monitoring

Swarm events are logged to `data/events.jsonl`:

```bash
# Monitor real-time events
tail -f data/events.jsonl | jq

# Count events by type
cat data/events.jsonl | jq -r '.event_type' | sort | uniq -c

# Check for suspicious patterns
grep -i "handoff\|escalate" data/events.jsonl
```

### Security Alerts

Set up monitoring for:

1. **Multiple 403 responses** - Possible attack attempt
2. **DEBUG=true in production** - Security misconfiguration
3. **Unusual behavior patterns** - Coordinated attack
4. **High rate limit hits** - DoS attempt

## Deployment Checklist

### Before Production Launch

- [ ] Set `PRODUCTION_MODE=true`
- [ ] Set `DEBUG=false`
- [ ] Generate strong `SECRET_KEY` (32+ characters)
- [ ] Review `ALLOW_AGENT_HANDOFF` setting
- [ ] Review `ALLOW_SOURCE_CITATION` setting
- [ ] Set `ENABLE_EASTER_EGGS=false`
- [ ] Test debug routes are blocked: `curl http://localhost:8000/swarm-status`
- [ ] Verify audit logging is working
- [ ] Set up log monitoring/alerting
- [ ] Review API key tiers and rate limits
- [ ] Enable HTTPS/TLS for API endpoints

### Regular Maintenance

- [ ] Rotate `SECRET_KEY` every 90 days
- [ ] Review audit logs weekly
- [ ] Monitor for suspicious patterns
- [ ] Update dependencies (security patches)
- [ ] Test security controls monthly
- [ ] Verify backup/recovery procedures

### Incident Response

If you suspect a security incident:

1. **Enable debug mode temporarily** to gather evidence:
   ```bash
   DEBUG=true
   ```

2. **Review recent audit logs**:
   ```bash
   tail -1000 src/memory/audit.jsonl | jq 'select(.timestamp > (now - 3600))'
   ```

3. **Check for suspicious behavior patterns**:
   ```bash
   python3 demo_security.py
   ```

4. **Disable compromised API keys** in `.roo/archonic-manifest.json`

5. **Rotate SECRET_KEY** immediately

6. **Restore DEBUG=false** after investigation

## Testing Security Controls

### Unit Tests

```bash
# Test security control logic
pytest tests/test_security_controls.py -v

# Test API endpoint protection
pytest tests/test_api_security.py -v
```

### Integration Tests

```bash
# Test in development mode (should allow all)
python3 demo_security.py

# Test in production mode (should block debug features)
PRODUCTION_MODE=true python3 demo_security.py

# Test with specific behaviors enabled
PRODUCTION_MODE=true ALLOW_AGENT_HANDOFF=true python3 demo_security.py
```

### Manual Security Testing

```bash
# Start server in production mode
PRODUCTION_MODE=true SECRET_KEY=test uvicorn src.api.causal_chain_server:app --port 8000

# Test debug routes are blocked (should return 403)
curl -i http://localhost:8000/swarm-status
curl -i http://localhost:8000/security-info

# Test production routes work (requires valid API key)
curl -i -H "X-API-Key: your-key" http://localhost:8000/legion-status
```

## FAQ

### Q: Can I enable debug routes in production temporarily?

**A**: Yes, but with extreme caution:

```bash
# Temporary debug access (disable immediately after)
DEBUG=true

# Better approach: Use SSH tunnel and local testing
ssh -L 8001:localhost:8000 production-server
# Access locally at http://localhost:8001
```

### Q: How do I know if someone is trying to exploit debug routes?

**A**: Monitor audit logs for 403 responses:

```bash
grep '"status_code":403' src/memory/audit.jsonl | jq
```

### Q: What if I need system info for troubleshooting?

**A**: Options:
1. Set `DEBUG=true` temporarily (disable immediately after)
2. Use dedicated monitoring tools (Prometheus, Grafana)
3. Query individual non-sensitive endpoints

### Q: Are Easter eggs a security risk?

**A**: No, Easter eggs are UI-only and don't affect model behavior. However, they may appear unprofessional in production. Disable with `ENABLE_EASTER_EGGS=false`.

### Q: Can I customize the blocked behavior patterns?

**A**: Yes, edit `src/api/security_controls.py`:

```python
# Add custom pattern
HANDOFF_PATTERNS = [
    "handoff to human",
    "your custom pattern here"
]
```

## Additional Resources

- [SECURITY.md](SECURITY.md) - Security policy and vulnerability reporting
- [README.md](README.md) - General project documentation
- `.env.example` - Environment variable reference
- `demo_security.py` - Interactive security demo

## Support

For security concerns or questions:
- Review [SECURITY.md](SECURITY.md) for vulnerability reporting
- Check audit logs: `src/memory/audit.jsonl`
- Run security demo: `python3 demo_security.py`
- Test configuration: `pytest tests/test_security_controls.py -v`

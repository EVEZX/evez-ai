# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :x:                |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Security Controls

### Production Mode

The system implements comprehensive security controls to protect debug routes and special agent behaviors in production environments.

#### Environment Variables

Configure security via the following environment variables (see `.env.example`):

- **`PRODUCTION_MODE`**: Set to `true` to enable production mode
  - Blocks all debug endpoints (`/navigation-ui`, `/swarm-status`, `/security-info`)
  - Restricts special agent behaviors
  - Disables Easter eggs by default

- **`DEBUG`**: Set to `true` to enable debug mode (overrides production restrictions)
  - Use with extreme caution in production
  - Should only be enabled for troubleshooting

- **`ALLOW_AGENT_HANDOFF`**: Controls handoff-to-human behavior in production
  - Default: `false` (blocked in production)
  - Set to `true` to allow agent handoff requests

- **`ALLOW_SOURCE_CITATION`**: Controls source citation requests in production
  - Default: `false` (blocked in production)
  - Set to `true` to allow "show sources" requests

- **`ENABLE_EASTER_EGGS`**: Controls UI Easter eggs in production
  - Default: `false` (disabled in production)
  - Enables console messages, animations, and hidden commands when `true`

### Protected Debug Routes

The following routes are blocked in production mode unless `DEBUG=true`:

- **`GET /navigation-ui`**: Quantum navigation visualization interface
- **`GET /navigation-ui/data`**: Raw navigation state data
- **`GET /swarm-status`**: Real-time swarm operational status
- **`GET /security-info`**: Security configuration information

### Agent Behavior Controls

The system detects and controls special agent behaviors:

#### Handoff to Human
- **Trigger patterns**: "handoff to human", "transfer to human", "escalate to human"
- **Production behavior**: Blocked unless `ALLOW_AGENT_HANDOFF=true`
- **Development behavior**: Always allowed

#### Source Citation
- **Trigger patterns**: "show sources", "cite sources", "list sources"
- **Production behavior**: Blocked unless `ALLOW_SOURCE_CITATION=true`
- **Development behavior**: Always allowed

#### Special Workflows
- **Trigger patterns**: "run workflow", "execute workflow", "trigger workflow"
- **Production behavior**: Blocked unless `ALLOW_AGENT_HANDOFF=true`
- **Development behavior**: Always allowed

#### System Info Reveal
- **Trigger patterns**: "system info", "reveal system", "show system"
- **Production behavior**: Always blocked (cannot be overridden)
- **Development behavior**: Always allowed

### Easter Egg Controls

UI-only features that don't affect the model:

- Console messages with Crustafarian tenets
- Hidden commands: `quantum_status`, `molt_history`, `swarm_info`, `crustafarian_tenets`
- Animations and visual effects

Easter eggs are disabled by default in production mode and require explicit opt-in via `ENABLE_EASTER_EGGS=true`.

### Best Practices

1. **Always set `PRODUCTION_MODE=true` in production deployments**
2. **Never enable `DEBUG=true` in production** (except for emergency troubleshooting)
3. **Keep `ALLOW_AGENT_HANDOFF=false`** unless your use case requires human escalation
4. **Review audit logs** in `src/memory/audit.jsonl` for security monitoring
5. **Use tier-based API keys** for graduated access control
6. **Rotate `SECRET_KEY`** periodically for HMAC signature security

## Reporting a Vulnerability

Use this section to tell people how to report a vulnerability.

Tell them where to go, how often they can expect to get an update on a
reported vulnerability, what to expect if the vulnerability is accepted or
declined, etc.

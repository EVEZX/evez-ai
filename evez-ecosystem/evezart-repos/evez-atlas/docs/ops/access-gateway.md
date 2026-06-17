# Access Gateway Pipeline (Local, Authorized)

This runbook documents the **access gateway pipeline** used to reach the causal chain API in a controlled environment. It is designed to keep navigation efficient while **preventing proxy bypass** and ensuring every request is authenticated, rate-limited, and auditable.

## Goals

- Provide a single, consistent entry point for API access.
- Prevent direct-to-service access that bypasses controls ("proxy bypass").
- Preserve auditability and enforce tiered access.
- Keep navigation efficient by using predictable routing and validated keys.
- Record what inventory checks have been completed before starting operations.

## Pipeline overview

1. **Client navigation**
   - Operators use approved clients (CLI or local tools) to send requests.
   - API keys map to access tiers.

2. **Gateway checks**
   - Requests include `X-API-Key` headers.
   - The gateway enforces tier-based rate limits and rejects unknown keys.
   - Responses are shaped to the caller's tier to reduce excess exposure.

3. **Service processing**
   - Requests are redacted based on tier policies.
   - Responses for `/resolve-awareness` are signed using HMAC.

4. **Audit logging**
   - Every call is recorded in `src/memory/audit.jsonl` with timestamp and tier.

## Proxy-bypass prevention checklist

- **Use a single entry point** for all API calls (localhost in lab settings).
- **Do not expose** the service directly on public interfaces without a reverse proxy.
- **Validate `X-API-Key`** at the gateway and refuse unauthenticated traffic.
- **Honor tier limits** to avoid privilege escalation via high-volume probing.
- **Track signature failures** and treat them as potential tampering.

## Local smoke test sequence

```bash
./scripts/deploy-all.sh

curl -H "X-API-Key: tier0_public" http://localhost:8000/legion-status
curl -H "X-API-Key: tier3_director" http://localhost:8000/legion-status

curl -X POST http://localhost:8000/resolve-awareness \
  -H "X-API-Key: tier3_director" \
  -H "Content-Type: application/json" \
  -d '{"output_id":"output-001"}'
```

## Inventory prerequisites

Document what is in scope before running the gateway pipeline:

- **Completed inventory checks**
  - Authorized targets and test ranges confirmed.
  - Approved API keys in `.roo/archonic-manifest.json`.
  - `SECRET_KEY` populated in the environment or `.env`.
- **Pending inventory checks**
  - Hostname/IP list confirmed in the lab environment.
  - Ownership approval documented for any newly added systems.

## Run steps (local operations started)

1. Start the causal chain server:

   ```bash
   ./scripts/deploy-all.sh
   ```

2. Confirm the gateway responds with tiered redaction:

   ```bash
   curl -H "X-API-Key: tier0_public" http://localhost:8000/legion-status
   curl -H "X-API-Key: tier3_director" http://localhost:8000/legion-status
   ```

3. Validate HMAC signatures on `/resolve-awareness` responses using a trusted client.

## Operational notes

- Rotate API keys by updating `.roo/archonic-manifest.json`.
- Keep `SECRET_KEY` secret; it is required for response signatures.
- Use `tools/audit_analyzer.py` to review tier activity.

## Failure modes to watch

- **401/403**: check API key mapping in `.roo/archonic-manifest.json`.
- **429**: tier rate limit exceeded; throttle the client.
- **500 signature errors**: `SECRET_KEY` missing or mismatched across services.

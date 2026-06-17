# EVEZ-OS Autonomizer — Cloudflare Deployment

## One-time setup

```bash
# Install deps
cd cloudflare-autonomizer
npm install

# Set Cloudflare credentials
export CLOUDFLARE_API_TOKEN=<your_token>
# OR: wrangler login (browser OAuth)

# Optional: set GitHub token for future state-pull feature
wrangler secret put GITHUB_TOKEN

# Deploy to Cloudflare Workers (300 PoPs globally)
wrangler deploy
```

## After deploy

Your Worker will be live at:
`https://evez-os-autonomizer.<your-subdomain>.workers.dev`

Update `hyperloop_state.json` with the live URL:
```json
"cloudflare_agent": {
  "live_url": "https://evez-os-autonomizer.YOUR_SUBDOMAIN.workers.dev"
}
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Status + version |
| `/state` | GET | Current hyperloop state (round, V, ceiling, fires) |
| `/ingest` | POST | Push round result from hyperloop cron |
| `/compute?N=<int>` | GET | Inline poly_c formula at edge (~1ms) |
| `/ws` | WS | Real-time state stream |

## Wire into hyperloop cron

After deploy, add to `hyperloop_state.json`:
```json
"cloudflare_agent": {
  "live_url": "https://evez-os-autonomizer.SUBDOMAIN.workers.dev",
  "ingest_on_every_tick": true
}
```

The hyperloop tick will POST to `/ingest` after each commit, broadcasting live state to all WebSocket subscribers.

## MCP (coming soon in cloudflare/agents SDK)

When Cloudflare ships MCP server support, EVEZ-OS becomes an MCP server —
any MCP-compatible AI client can query `/state` and subscribe to the hyperloop.

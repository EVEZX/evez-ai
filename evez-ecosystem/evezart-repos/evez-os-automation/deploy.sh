#!/usr/bin/env bash
set -e

echo "⚡ EVEZ-OS FULLSTACK DEPLOYMENT"
echo ""

if [ ! -f .env ]; then echo "❌ Missing .env — cp .env.example .env first"; exit 1; fi
source .env

echo "── STEP 1: Verifying Supabase tables ──"
curl -sf "${SUPABASE_URL}/rest/v1/transactions?select=count&limit=1" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" -H "apikey: ${SUPABASE_KEY}" > /dev/null \
  && echo "✅ transactions" || echo "⚠️  transactions not found"
curl -sf "${SUPABASE_URL}/rest/v1/agent_queue?select=count&limit=1" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" -H "apikey: ${SUPABASE_KEY}" > /dev/null \
  && echo "✅ agent_queue" || echo "⚠️  agent_queue not found"
curl -sf "${SUPABASE_URL}/rest/v1/github_sync_log?select=count&limit=1" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" -H "apikey: ${SUPABASE_KEY}" > /dev/null \
  && echo "✅ github_sync_log" || echo "⚠️  github_sync_log not found"
curl -sf "${SUPABASE_URL}/rest/v1/qualia_spine?select=count&limit=1" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" -H "apikey: ${SUPABASE_KEY}" > /dev/null \
  && echo "✅ qualia_spine" || echo "⚠️  qualia_spine not found"

echo ""
echo "── STEP 2: Register Stripe webhook ──"
if [ -n "${STRIPE_SECRET_KEY}" ]; then
  RESP=$(curl -sf -u "${STRIPE_SECRET_KEY}:" https://api.stripe.com/v1/webhook_endpoints \
    -d "url=${WEBHOOK_BASE_URL}/stripe/payment-success" \
    -d "enabled_events[]=charge.succeeded" \
    -d "enabled_events[]=payment_intent.succeeded" 2>&1 || echo "SKIP")
  echo "$RESP" | grep -q '"id"' && echo "✅ Stripe webhook registered" || echo "⚠️  Stripe: $RESP"
else echo "⚠️  STRIPE_SECRET_KEY not set — skipping"; fi

echo ""
echo "── STEP 3: Start orchestrator ──"
NODE_ENV=production node evez-automation-orchestrator.js &
ORCH_PID=$!
echo "✅ Orchestrator PID: $ORCH_PID"
echo $ORCH_PID > .orchestrator.pid

echo ""
echo "── STEP 4: Start dashboard ──"
node evez-monitoring-dashboard.js &
DASH_PID=$!
echo "✅ Dashboard PID: $DASH_PID"
echo $DASH_PID > .dashboard.pid

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ EVEZ-OS FULLY OPERATIONAL                                ║"
echo "║                                                              ║"
echo "║  Orchestrator: ${WEBHOOK_BASE_URL}/health                ║"
echo "║  Dashboard:    ${WEBHOOK_BASE_URL}:4000/dashboard.html   ║"
echo "║                                                              ║"
echo "║  Register GitHub webhooks:                                   ║"
echo "║  URL: ${WEBHOOK_BASE_URL}/github/push                    ║"
echo "║  Secret: \${GITHUB_WEBHOOK_SECRET}                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"

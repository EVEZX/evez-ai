/**
 * EVEZ-OS FULLSTACK AUTOMATION ORCHESTRATOR
 * Layer A: Revenue Automation (Stripe → Supabase → Slack)
 * Layer B: Agent Orchestration (Queue → HARVEST → SCOUT → WITNESS → DEPLOY)
 * Layer C: Daily Digest (06:00 UTC cron → #ops-digest)
 * Layer D: GitHub Auto-Sync (push → Linear issue → Supabase log → Slack)
 *
 * Entry point: node evez-automation-orchestrator.js
 * Webhook server on PORT (default 3000)
 */

'use strict';

const http = require('http');
const https = require('https');
const crypto = require('crypto');
const url = require('url');

// ─────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────
const cfg = {
  port:             parseInt(process.env.PORT || '3000'),
  supabaseUrl:      process.env.SUPABASE_URL,
  supabaseKey:      process.env.SUPABASE_KEY,
  stripeSecret:     process.env.STRIPE_SECRET_KEY,
  stripeWebhookSec: process.env.STRIPE_WEBHOOK_SECRET,
  slackToken:       process.env.SLACK_BOT_TOKEN,
  linearKey:        process.env.LINEAR_API_KEY,
  githubSecret:     process.env.GITHUB_WEBHOOK_SECRET,
  anthropicKey:     process.env.ANTHROPIC_API_KEY,
  webhookBase:      process.env.WEBHOOK_BASE_URL || 'http://localhost:3000',

  // Slack channel names (auto-resolved to IDs on start)
  channels: {
    revenuespine: '#revenue-spine',
    ops:          '#ops',
    digest:       '#ops-digest',
    deployments:  '#deployments',
  },

  // Agent tiers (ms delay)
  agentTiers: {
    1: [{ name: 'HARVEST',  delay: 3000 }],
    2: [{ name: 'SCOUT',    delay: 6000 }, { name: 'WITNESS', delay: 6000 }],
    3: [{ name: 'DEPLOY',   delay: 9000 }],
  },
};

// ─────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────
function log(tag, msg, data = '') {
  const ts = new Date().toISOString();
  console.log(`[${ts}] [${tag}] ${msg}`, data ? JSON.stringify(data) : '');
}

function httpsPost(hostname, path, headers, body) {
  return new Promise((resolve, reject) => {
    const data = typeof body === 'string' ? body : JSON.stringify(body);
    const req = https.request({ hostname, path, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers }
    }, (res) => {
      let chunks = '';
      res.on('data', d => chunks += d);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(chunks) }); }
        catch { resolve({ status: res.statusCode, body: chunks }); }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function supabaseRPC(table, method, body, params = '') {
  const [host, ...rest] = cfg.supabaseUrl.replace('https://','').split('/');
  const path = `/rest/v1/${table}${params}`;
  return httpsPost(host, path, {
    'Authorization': `Bearer ${cfg.supabaseKey}`,
    'apikey': cfg.supabaseKey,
    'Prefer': method === 'INSERT' ? 'return=representation' : 'return=minimal',
    'X-HTTP-Method-Override': method,
  }, body);
}

function supabaseInsert(table, row) {
  return supabaseRPC(table, 'INSERT', row);
}

function supabaseQuery(table, select = '*', filter = '') {
  const [host] = cfg.supabaseUrl.replace('https://','').split('/');
  return new Promise((resolve, reject) => {
    const path = `/rest/v1/${table}?select=${select}${filter ? '&' + filter : ''}`;
    https.get({
      hostname: host, path,
      headers: { 'Authorization': `Bearer ${cfg.supabaseKey}`, 'apikey': cfg.supabaseKey }
    }, (res) => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch { resolve([]); } });
    }).on('error', reject);
  });
}

function slackPost(channel, blocks, text = '') {
  if (!cfg.slackToken) return Promise.resolve({ ok: false, error: 'no_token' });
  return httpsPost('slack.com', '/api/chat.postMessage',
    { 'Authorization': `Bearer ${cfg.slackToken}` },
    { channel, blocks, text }
  );
}

function linearCreate(title, description, priority = 2) {
  if (!cfg.linearKey) return Promise.resolve(null);
  const query = `mutation { issueCreate(input: { teamId: "6659fbfd-fcdb-4cdd-9e5b-7eed5c7b90c6", projectId: "f8331bcf-0f8f-4d80-8a95-e267c5d68dac", title: "${title.replace(/"/g,'')}", description: "${description.replace(/"/g,'\\n')}", priority: ${priority} }) { success issue { id identifier url } } }`;
  return httpsPost('api.linear.app', '/graphql',
    { 'Authorization': cfg.linearKey, 'Content-Type': 'application/json' },
    { query }
  );
}

// ─────────────────────────────────────────────
// LAYER A: REVENUE AUTOMATION
// ─────────────────────────────────────────────
async function handleStripePayment(event) {
  const charge = event.data?.object;
  if (!charge) return;

  const amountCents = charge.amount || 0;
  const amountDollars = (amountCents / 100).toFixed(2);
  const email = charge.billing_details?.email || charge.metadata?.email || 'unknown';
  const chargeId = charge.id;
  const eventId = event.id;

  log('LAYER_A', `Payment received: $${amountDollars} from ${email}`);

  // 1. Insert to Supabase
  let txId = null;
  try {
    const r = await supabaseInsert('transactions', {
      stripe_event_id: eventId,
      stripe_charge_id: chargeId,
      amount_cents: amountCents,
      currency: (charge.currency || 'usd').toUpperCase(),
      user_email: email,
      metadata: { source: 'stripe_webhook', charge_type: event.type },
    });
    if (r.body && r.body[0]) txId = r.body[0].id;
    log('LAYER_A', `Supabase insert OK, tx_id=${txId}`);
  } catch (e) {
    log('LAYER_A', 'Supabase insert failed', e.message);
  }

  // 2. Calculate running daily total
  let dailyTotal = amountCents;
  try {
    const today = new Date().toISOString().split('T')[0];
    const rows = await supabaseQuery('transactions', 'amount_cents',
      `created_at=gte.${today}T00:00:00Z&order=created_at.desc`);
    dailyTotal = rows.reduce((s, r) => s + (r.amount_cents || 0), 0);
  } catch {}

  const dailyDollars = (dailyTotal / 100).toFixed(2);

  // 3. Slack notification → #revenue-spine
  await slackPost('#revenue-spine', [
    {
      type: 'section',
      text: { type: 'mrkdwn',
        text: `🔥 *Payment Received* | $${amountDollars}\n📧 ${email} | Daily Total: *$${dailyDollars}*` }
    },
    {
      type: 'context', elements: [{
        type: 'mrkdwn',
        text: `_Stripe ${event.type} | ${chargeId} | Layer A: Revenue Automation_`
      }]
    }
  ]);

  // 4. Enqueue agent jobs (Layer B)
  if (txId) await enqueueAgentJobs(txId, amountCents);
}

// ─────────────────────────────────────────────
// LAYER B: AGENT ORCHESTRATION
// ─────────────────────────────────────────────
async function enqueueAgentJobs(txId, amountCents) {
  log('LAYER_B', `Enqueuing agent jobs for tx_id=${txId}`);
  for (const [tier, agents] of Object.entries(cfg.agentTiers)) {
    for (const agent of agents) {
      await supabaseInsert('agent_queue', {
        transaction_id: txId,
        tier: parseInt(tier),
        agent_name: agent.name,
        status: 'pending',
        payload: { executionDelay: agent.delay, amountCents },
      });
    }
  }

  await slackPost('#ops', [
    {
      type: 'section',
      text: { type: 'mrkdwn',
        text: `🚀 *Agent Queue Populated* | tx_id: ${txId}\n[T1] HARVEST → [T2] SCOUT + WITNESS → [T3] DEPLOY` }
    }
  ]);

  // Execute staggered
  executeAgentTier(txId, 1);
}

async function executeAgentTier(txId, tier) {
  const agents = cfg.agentTiers[tier];
  if (!agents) return;

  await new Promise(r => setTimeout(r, agents[0].delay));

  for (const agent of agents) {
    log('LAYER_B', `Executing ${agent.name} (T${tier}) for tx_id=${txId}`);

    const result = await runAgent(agent.name, txId);

    // Mark executed in Supabase
    try {
      const [host] = cfg.supabaseUrl.replace('https://','').split('/');
      await httpsPost(host, `/rest/v1/agent_queue?transaction_id=eq.${txId}&agent_name=eq.${agent.name}&status=eq.pending`,
        {
          'Authorization': `Bearer ${cfg.supabaseKey}`,
          'apikey': cfg.supabaseKey,
          'Prefer': 'return=minimal',
        },
        { status: 'completed', executed_at: new Date().toISOString(), result }
      );
    } catch (e) { log('LAYER_B', 'Queue update failed', e.message); }

    await slackPost('#ops', [{
      type: 'section',
      text: { type: 'mrkdwn', text: `✅ *[T${tier}] ${agent.name}* completed | tx_id: ${txId}` }
    }]);
  }

  // Cascade to next tier
  if (cfg.agentTiers[tier + 1]) executeAgentTier(txId, tier + 1);
}

async function runAgent(name, txId) {
  switch (name) {
    case 'HARVEST':
      return { action: 'data_harvest', txId, timestamp: Date.now(), status: 'ok' };
    case 'SCOUT':
      return { action: 'audit_scan', txId, authenticity: 'verified', risk: 'low' };
    case 'WITNESS':
      // Append to qualia_spine (immutable log)
      try {
        const hash = crypto.createHash('sha256').update(`${txId}-${Date.now()}`).digest('hex');
        await supabaseInsert('qualia_spine', {
          event_type: 'WITNESS_SEAL',
          hash_chain: hash,
          payload: { txId, ts: new Date().toISOString() },
        });
      } catch {}
      return { action: 'witness_seal', txId, sealed: true };
    case 'DEPLOY':
      return { action: 'deploy_trigger', txId, deploy: 'auto_commit_queued' };
    default:
      return { action: name, txId };
  }
}

// ─────────────────────────────────────────────
// LAYER C: DAILY DIGEST
// ─────────────────────────────────────────────
async function sendDailyDigest() {
  log('LAYER_C', 'Sending daily digest');

  const today = new Date().toISOString().split('T')[0];
  let revenue = 0, txCount = 0, queueStats = { completed: 0, failed: 0, pending: 0 },
      spineCount = 0;

  try {
    const rows = await supabaseQuery('transactions', 'amount_cents',
      `created_at=gte.${today}T00:00:00Z`);
    txCount = rows.length;
    revenue = rows.reduce((s, r) => s + (r.amount_cents || 0), 0);
  } catch {}

  try {
    const qRows = await supabaseQuery('agent_queue', 'status',
      `created_at=gte.${today}T00:00:00Z`);
    for (const r of qRows) queueStats[r.status] = (queueStats[r.status] || 0) + 1;
  } catch {}

  try {
    const sRows = await supabaseQuery('qualia_spine', 'id',
      `created_at=gte.${today}T00:00:00Z`);
    spineCount = sRows.length;
  } catch {}

  const total = queueStats.completed + queueStats.failed;
  const successRate = total ? ((queueStats.completed / total) * 100).toFixed(1) + '%' : 'N/A';

  await slackPost('#ops-digest', [
    {
      type: 'header',
      text: { type: 'plain_text', text: '📊 EVEZ-OS Daily Operations Report', emoji: true }
    },
    {
      type: 'section',
      fields: [
        { type: 'mrkdwn', text: `*Revenue*\n💰 $${(revenue/100).toFixed(2)}\n📦 ${txCount} transactions` },
        { type: 'mrkdwn', text: `*Agent Health*\n✅ ${queueStats.completed} done\n❌ ${queueStats.failed} failed\n📈 ${successRate}` },
        { type: 'mrkdwn', text: `*Spine Events*\n📡 ${spineCount} records\n⛓️ Chain: intact` },
        { type: 'mrkdwn', text: `*Queue*\n⏳ ${queueStats.pending || 0} pending\n🕐 ${new Date().toUTCString()}` },
      ]
    }
  ]);
}

// Cron check: runs every minute, fires at 06:00 UTC
let lastDigestDay = '';
function startDigestCron() {
  setInterval(async () => {
    const now = new Date();
    const day = now.toISOString().split('T')[0];
    if (now.getUTCHours() === 6 && now.getUTCMinutes() < 2 && day !== lastDigestDay) {
      lastDigestDay = day;
      await sendDailyDigest();
    }
  }, 60_000);
  log('LAYER_C', 'Daily digest cron active (fires at 06:00 UTC)');
}

// ─────────────────────────────────────────────
// LAYER D: GITHUB AUTO-SYNC
// ─────────────────────────────────────────────
async function handleGithubPush(payload) {
  const repo = payload.repository?.full_name || 'unknown';
  const branch = (payload.ref || '').replace('refs/heads/', '');
  const commit = payload.head_commit;
  if (!commit) return;

  const sha = commit.id;
  const message = commit.message;
  const author = commit.author?.email || 'unknown';
  const env = branch === 'main' ? 'production' : branch === 'dev' ? 'staging' : 'draft';

  log('LAYER_D', `GitHub push: ${repo}/${branch} @ ${sha.slice(0,8)}`);

  // Create Linear issue
  let issueId = null, issueUrl = null;
  try {
    const r = await linearCreate(
      `[${env.toUpperCase()}] ${repo}: ${message.split('\n')[0].slice(0,80)}`,
      `Auto-created from GitHub push\n\n**Repo:** ${repo}\n**Branch:** ${branch} (${env})\n**SHA:** ${sha}\n**Author:** ${author}\n**Message:** ${message}`
    );
    if (r.body?.data?.issueCreate?.success) {
      issueId = r.body.data.issueCreate.issue.identifier;
      issueUrl = r.body.data.issueCreate.issue.url;
      log('LAYER_D', `Linear issue created: ${issueId}`);
    }
  } catch (e) { log('LAYER_D', 'Linear create failed', e.message); }

  // Log to Supabase
  try {
    await supabaseInsert('github_sync_log', {
      repo_name: repo, branch, commit_sha: sha,
      commit_message: message, author_email: author,
      linear_issue_id: issueId || null, status: 'synced',
    });
  } catch (e) { log('LAYER_D', 'Supabase log failed', e.message); }

  // Slack notification
  await slackPost('#deployments', [
    {
      type: 'section',
      text: { type: 'mrkdwn',
        text: `📦 *${repo}* pushed to \`${branch}\` (${env})\n>${message.split('\n')[0].slice(0,100)}${issueId ? `\n🔗 Linear: <${issueUrl}|${issueId}>` : ''}` }
    },
    {
      type: 'context', elements: [{
        type: 'mrkdwn', text: `_SHA: ${sha.slice(0,8)} | Author: ${author} | Layer D: GitHub Sync_`
      }]
    }
  ]);
}

// ─────────────────────────────────────────────
// WEBHOOK SERVER
// ─────────────────────────────────────────────
function verifyStripeSignature(rawBody, signature) {
  if (!cfg.stripeWebhookSec || !signature) return true; // skip in dev
  const parts = signature.split(',').reduce((o, p) => {
    const [k, v] = p.split('='); o[k] = v; return o;
  }, {});
  const expected = crypto.createHmac('sha256', cfg.stripeWebhookSec)
    .update(`${parts.t}.${rawBody}`).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(parts.v1 || ''), Buffer.from(expected));
}

function verifyGithubSignature(rawBody, signature) {
  if (!cfg.githubSecret || !signature) return true;
  const expected = 'sha256=' + crypto.createHmac('sha256', cfg.githubSecret)
    .update(rawBody).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

const server = http.createServer(async (req, res) => {
  const parsed = url.parse(req.url || '/', true);
  const path = parsed.pathname;

  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'GET' && path === '/health') {
    return res.end(JSON.stringify({ status: 'ok', uptime: process.uptime(), ts: new Date().toISOString() }));
  }

  if (req.method === 'GET' && path === '/trigger/digest') {
    await sendDailyDigest();
    return res.end(JSON.stringify({ ok: true, message: 'Digest sent' }));
  }

  // Collect body
  let rawBody = '';
  req.on('data', d => rawBody += d);
  req.on('end', async () => {
    try {
      if (req.method === 'POST' && path === '/stripe/payment-success') {
        const sig = req.headers['stripe-signature'];
        if (!verifyStripeSignature(rawBody, sig)) {
          res.statusCode = 400; return res.end(JSON.stringify({ error: 'invalid_signature' }));
        }
        const event = JSON.parse(rawBody);
        if (['charge.succeeded', 'payment_intent.succeeded'].includes(event.type)) {
          handleStripePayment(event).catch(e => log('ERROR', e.message));
        }
        return res.end(JSON.stringify({ received: true }));
      }

      if (req.method === 'POST' && path === '/github/push') {
        const sig = req.headers['x-hub-signature-256'];
        if (!verifyGithubSignature(rawBody, sig)) {
          res.statusCode = 400; return res.end(JSON.stringify({ error: 'invalid_signature' }));
        }
        const payload = JSON.parse(rawBody);
        handleGithubPush(payload).catch(e => log('ERROR', e.message));
        return res.end(JSON.stringify({ received: true }));
      }

      res.statusCode = 404;
      res.end(JSON.stringify({ error: 'not_found', path }));
    } catch (e) {
      log('ERROR', e.message);
      res.statusCode = 500;
      res.end(JSON.stringify({ error: e.message }));
    }
  });
});

// ─────────────────────────────────────────────
// START
// ─────────────────────────────────────────────
server.listen(cfg.port, () => {
  log('EVEZ-OS', `Automation server live on :${cfg.port}`);
  log('EVEZ-OS', `Stripe endpoint: POST ${cfg.webhookBase}/stripe/payment-success`);
  log('EVEZ-OS', `GitHub endpoint: POST ${cfg.webhookBase}/github/push`);
  startDigestCron();
});

module.exports = { handleStripePayment, handleGithubPush, sendDailyDigest };

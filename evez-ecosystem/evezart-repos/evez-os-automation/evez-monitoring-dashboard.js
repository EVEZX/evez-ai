/**
 * EVEZ-OS Monitoring Dashboard
 * Express API + live HTML dashboard (5-second refresh)
 * Deploy to Vercel: vercel deploy --prod
 */
'use strict';

const http = require('http');
const https = require('https');

const cfg = {
  port:        parseInt(process.env.PORT || '4000'),
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseKey: process.env.SUPABASE_KEY,
  linearKey:   process.env.LINEAR_API_KEY,
};

function supabaseGet(table, select, filter = '') {
  return new Promise((resolve) => {
    if (!cfg.supabaseUrl) return resolve([]);
    const [host] = cfg.supabaseUrl.replace('https://','').split('/');
    const path = `/rest/v1/${table}?select=${select}${filter ? '&' + filter : ''}`;
    https.get({ hostname: host, path,
      headers: { 'Authorization': `Bearer ${cfg.supabaseKey}`, 'apikey': cfg.supabaseKey }
    }, (res) => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch { resolve([]); } });
    }).on('error', () => resolve([]));
  });
}

async function getMetrics() {
  const today = new Date().toISOString().split('T')[0];
  const week = new Date(Date.now() - 7*86400*1000).toISOString();

  const [txRows, qRows, sRows, ghRows] = await Promise.all([
    supabaseGet('transactions', 'amount_cents,created_at', `created_at=gte.${today}T00:00:00Z`),
    supabaseGet('agent_queue', 'status,tier,agent_name', `created_at=gte.${today}T00:00:00Z`),
    supabaseGet('qualia_spine', 'id,event_type', `created_at=gte.${today}T00:00:00Z`),
    supabaseGet('github_sync_log', 'repo_name,branch,commit_sha,linear_issue_id,created_at', `created_at=gte.${week}`),
  ]);

  const revenue = txRows.reduce((s, r) => s + (r.amount_cents || 0), 0);
  const qDone = qRows.filter(r => r.status === 'completed').length;
  const qFail = qRows.filter(r => r.status === 'failed').length;
  const qPend = qRows.filter(r => r.status === 'pending').length;

  return {
    revenue: { total: revenue, dollars: (revenue/100).toFixed(2), txCount: txRows.length },
    queue:   { completed: qDone, failed: qFail, pending: qPend,
               successRate: (qDone + qFail > 0) ? ((qDone/(qDone+qFail))*100).toFixed(1)+'%' : 'N/A' },
    spine:   { count: sRows.length },
    github:  { syncs: ghRows.length, repos: [...new Set(ghRows.map(r => r.repo_name))] },
    ts:      new Date().toISOString(),
  };
}

const dashboardHtml = (metrics) => `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EVEZ-OS Dashboard</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0a0a0a; color: #e0e0e0; font-family: 'Courier New', monospace; padding: 20px; }
h1 { color: #ff4444; font-size: 1.4rem; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }
.card { background: #111; border: 1px solid #222; border-radius: 8px; padding: 16px; }
.card .label { font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.card .value { font-size: 1.8rem; font-weight: bold; color: #00ff88; }
.card .sub { font-size: 0.8rem; color: #555; margin-top: 4px; }
.status { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #00ff88; margin-right: 6px; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.ts { font-size: 0.7rem; color: #333; text-align: right; margin-top: 20px; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; }
th, td { text-align: left; padding: 6px 8px; font-size: 0.78rem; border-bottom: 1px solid #1a1a1a; }
th { color: #555; font-weight: normal; }
</style>
<meta http-equiv="refresh" content="5">
</head>
<body>
<h1><span class="status"></span>EVEZ-OS OPERATOR DASHBOARD</h1>
<div class="grid">
  <div class="card">
    <div class="label">Daily Revenue</div>
    <div class="value">$${metrics.revenue.dollars}</div>
    <div class="sub">${metrics.revenue.txCount} transactions today</div>
  </div>
  <div class="card">
    <div class="label">Agent Success Rate</div>
    <div class="value">${metrics.queue.successRate}</div>
    <div class="sub">${metrics.queue.completed} done · ${metrics.queue.failed} failed · ${metrics.queue.pending} pending</div>
  </div>
  <div class="card">
    <div class="label">Spine Events (today)</div>
    <div class="value">${metrics.spine.count}</div>
    <div class="sub">Immutable QUALIA records</div>
  </div>
  <div class="card">
    <div class="label">GitHub Syncs (7d)</div>
    <div class="value">${metrics.github.syncs}</div>
    <div class="sub">${metrics.github.repos.slice(0,3).join(', ')}${metrics.github.repos.length > 3 ? ' +more' : ''}</div>
  </div>
</div>
<div class="ts">Last updated: ${metrics.ts} · Auto-refresh: 5s</div>
</body>
</html>`;

const server = http.createServer(async (req, res) => {
  const path = (req.url || '/').split('?')[0];

  if (path === '/health') {
    res.setHeader('Content-Type','application/json');
    return res.end(JSON.stringify({ status:'ok', ts: new Date().toISOString() }));
  }

  if (path === '/api/metrics' || path === '/api/revenue/daily') {
    const m = await getMetrics();
    res.setHeader('Content-Type','application/json');
    return res.end(JSON.stringify(m));
  }

  if (path === '/dashboard.html' || path === '/') {
    const m = await getMetrics();
    res.setHeader('Content-Type','text/html');
    return res.end(dashboardHtml(m));
  }

  res.statusCode = 404;
  res.setHeader('Content-Type','application/json');
  res.end(JSON.stringify({ error: 'not_found' }));
});

server.listen(cfg.port, () => {
  console.log(`[EVEZ-DASH] Dashboard on :${cfg.port} → /dashboard.html`);
});

module.exports = { getMetrics };

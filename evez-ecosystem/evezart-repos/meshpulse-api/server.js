import express from 'express';
import { createClient } from '@supabase/supabase-js';
import { createHash, randomBytes } from 'crypto';

const app = express();
app.use(express.json());
const supabase = createClient(process.env.SUPABASE_URL||'', process.env.SUPABASE_SERVICE_KEY||'');

async function auth(req) {
  const k = req.headers['x-api-key'];
  if (!k) return { r: null, e: { s: 401, b: { error: 'Missing x-api-key' } } };
  const h = createHash('sha256').update(k).digest('hex');
  const { data } = await supabase.from('api_keys').select('*').eq('key_hash', h).eq('is_active', true).single();
  if (!data) return { r: null, e: { s: 403, b: { error: 'Invalid API key' } } };
  return { r: data, e: null };
}

// Health
app.get('/api/health', (_, res) => res.json({ status: 'operational', service: 'MeshPulse Uptime Monitor', version: '1.0.0', timestamp: new Date().toISOString() }));

// Generate key
app.post('/api/keys', async (req, res) => {
  const { name, email } = req.body || {};
  if (!name) return res.status(400).json({ error: 'name required' });
  const raw = `mp_${randomBytes(24).toString('hex')}`;
  const { data, error } = await supabase.schema('meshpulse').from('api_keys').insert({ key_hash: createHash('sha256').update(raw).digest('hex'), name, owner_email: email, tier: 'free', max_monitors: 5, check_interval_min: 300, monthly_quota: 10000 }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json({ api_key: raw, key_id: data.id, name: data.name, limits: { max_monitors: 5, check_interval_min: '5 min', monthly_quota: 10000 } });
});

// Create monitor
app.post('/api/monitors', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { url, name, check_interval_seconds = 300, expected_status = 200 } = req.body || {};
  if (!url || !name) return res.status(400).json({ error: 'url and name required' });
  const { count } = await supabase.schema('meshpulse').from('monitors').select('*', { count: 'exact', head: true }).eq('api_key_id', r.id).eq('is_active', true);
  if (count >= r.max_monitors) return res.status(429).json({ error: 'Monitor limit reached', max: r.max_monitors });
  const { data, error } = await supabase.schema('meshpulse').from('monitors').insert({ api_key_id: r.id, url, name, check_interval_seconds, expected_status }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json(data);
});

// List monitors
app.get('/api/monitors', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { data } = await supabase.schema('meshpulse').from('monitors').select('*').eq('api_key_id', r.id).order('created_at', { ascending: false });
  res.json({ monitors: data || [] });
});

// Check now
app.post('/api/monitors/:id/check', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { data: mon } = await supabase.schema('meshpulse').from('monitors').select('*').eq('id', req.params.id).eq('api_key_id', r.id).single();
  if (!mon) return res.status(404).json({ error: 'Monitor not found' });
  const started = Date.now();
  try {
    const fr = await fetch(mon.url, { signal: AbortSignal.timeout(mon.timeout_ms || 10000), headers: { 'User-Agent': 'MeshPulse/1.0' } });
    const ms = Date.now() - started;
    const isUp = fr.status === mon.expected_status;
    await supabase.schema('meshpulse').from('check_logs').insert({ monitor_id: mon.id, status_code: fr.status, response_time_ms: ms, is_up: isUp });
    const newTotal = mon.total_checks + 1;
    const newFail = isUp ? mon.total_failures : mon.total_failures + 1;
    await supabase.schema('meshpulse').from('monitors').update({ last_check_at: new Date().toISOString(), last_status: fr.status, last_response_ms: ms, total_checks: newTotal, total_failures: newFail, uptime_percent: (((newTotal - newFail) / newTotal) * 100).toFixed(2) }).eq('id', mon.id);
    if (!isUp) await supabase.schema('meshpulse').from('incidents').insert({ monitor_id: mon.id, error_message: `Expected ${mon.expected_status}, got ${fr.status}` });
    res.json({ monitor: mon.name, url: mon.url, status_code: fr.status, response_time_ms: ms, is_up: isUp, uptime_percent: (((newTotal - newFail) / newTotal) * 100).toFixed(2) });
  } catch (err) {
    const ms = Date.now() - started;
    await supabase.schema('meshpulse').from('check_logs').insert({ monitor_id: mon.id, status_code: 0, response_time_ms: ms, is_up: false, error_message: err.message });
    await supabase.schema('meshpulse').from('incidents').insert({ monitor_id: mon.id, error_message: err.message });
    res.json({ monitor: mon.name, url: mon.url, status_code: 0, response_time_ms: ms, is_up: false, error: err.message });
  }
});

// Incidents
app.get('/api/monitors/:id/incidents', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { data } = await supabase.schema('meshpulse').from('incidents').select('*').eq('monitor_id', req.params.id).order('started_at', { ascending: false }).limit(50);
  res.json({ incidents: data || [] });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`📡 MeshPulse running on :${PORT}`));

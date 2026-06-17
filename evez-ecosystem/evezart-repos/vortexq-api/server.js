import express from 'express';
import { createClient } from '@supabase/supabase-js';
import { createHash, randomBytes } from 'crypto';

const app = express();
app.use(express.json({ limit: '256kb' }));
const supabase = createClient(process.env.SUPABASE_URL||'', process.env.SUPABASE_SERVICE_KEY||'');

async function auth(req) {
  const k = req.headers['x-api-key'];
  if (!k) return { r: null, e: { s: 401, b: { error: 'Missing x-api-key' } } };
  const h = createHash('sha256').update(k).digest('hex');
  const { data } = await supabase.schema('vortexq').from('api_keys').select('*').eq('key_hash', h).eq('is_active', true).single();
  if (!data) return { r: null, e: { s: 403, b: { error: 'Invalid API key' } } };
  return { r: data, e: null };
}

app.get('/api/health', (_, res) => res.json({ status: 'operational', service: 'VortexQ Job Queue', version: '1.0.0', timestamp: new Date().toISOString() }));

app.post('/api/keys', async (req, res) => {
  const { name, email } = req.body || {};
  if (!name) return res.status(400).json({ error: 'name required' });
  const raw = `vq_${randomBytes(24).toString('hex')}`;
  const { data, error } = await supabase.schema('vortexq').from('api_keys').insert({ key_hash: createHash('sha256').update(raw).digest('hex'), name, owner_email: email }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json({ api_key: raw, key_id: data.id, limits: { max_queues: 3, monthly_jobs: 5000, max_payload: '64KB' } });
});

// Submit job
app.post('/api/jobs', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { queue = 'default', payload, priority = 0, max_attempts = 3, webhook_url, delay_seconds } = req.body || {};
  if (!payload) return res.status(400).json({ error: 'payload required' });
  const payloadSize = JSON.stringify(payload).length;
  if (payloadSize > r.max_payload_bytes) return res.status(413).json({ error: `Payload too large (${payloadSize} > ${r.max_payload_bytes} bytes)` });
  const scheduled_for = delay_seconds ? new Date(Date.now() + delay_seconds * 1000).toISOString() : new Date().toISOString();
  const { data, error } = await supabase.schema('vortexq').from('jobs').insert({ api_key_id: r.id, queue, payload, priority, max_attempts, webhook_url, scheduled_for }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json({ job_id: data.id, queue, status: 'pending', priority, scheduled_for, webhook_url: webhook_url ? 'configured' : null, created_at: data.created_at });
});

// Get job status
app.get('/api/jobs/:id', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { data } = await supabase.schema('vortexq').from('jobs').select('*').eq('id', req.params.id).eq('api_key_id', r.id).single();
  if (!data) return res.status(404).json({ error: 'Job not found' });
  res.json(data);
});

// Pull next job from queue (for workers)
app.post('/api/queues/:queue/pull', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { data } = await supabase.schema('vortexq').from('jobs').select('*').eq('api_key_id', r.id).eq('queue', req.params.queue).eq('status', 'pending').lte('scheduled_for', new Date().toISOString()).order('priority', { ascending: false }).order('created_at', { ascending: true }).limit(1).single();
  if (!data) return res.json({ job: null, message: 'Queue empty' });
  await supabase.schema('vortexq').from('jobs').update({ status: 'processing', started_at: new Date().toISOString(), attempts: data.attempts + 1 }).eq('id', data.id);
  res.json({ job: { id: data.id, payload: data.payload, queue: data.queue, attempt: data.attempts + 1, max_attempts: data.max_attempts } });
});

// Complete job
app.post('/api/jobs/:id/complete', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { result } = req.body || {};
  const { data } = await supabase.schema('vortexq').from('jobs').update({ status: 'completed', result: result || {}, completed_at: new Date().toISOString() }).eq('id', req.params.id).eq('api_key_id', r.id).select().single();
  if (!data) return res.status(404).json({ error: 'Job not found' });
  if (data.webhook_url) { fetch(data.webhook_url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'job.completed', job_id: data.id, result }) }).catch(() => {}); }
  res.json({ job_id: data.id, status: 'completed', completed_at: data.completed_at });
});

// Fail job
app.post('/api/jobs/:id/fail', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { error_message } = req.body || {};
  const { data: job } = await supabase.schema('vortexq').from('jobs').select('*').eq('id', req.params.id).eq('api_key_id', r.id).single();
  if (!job) return res.status(404).json({ error: 'Job not found' });
  if (job.attempts < job.max_attempts) {
    await supabase.schema('vortexq').from('jobs').update({ status: 'pending', error_message }).eq('id', job.id);
    res.json({ job_id: job.id, status: 'retrying', attempt: job.attempts, max_attempts: job.max_attempts });
  } else {
    await supabase.schema('vortexq').from('jobs').update({ status: 'failed', error_message, completed_at: new Date().toISOString() }).eq('id', job.id);
    await supabase.schema('vortexq').from('dead_letter').insert({ original_job_id: job.id, queue: job.queue, payload: job.payload, error_message });
    if (job.webhook_url) { fetch(job.webhook_url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'job.failed', job_id: job.id, error_message }) }).catch(() => {}); }
    res.json({ job_id: job.id, status: 'failed', moved_to_dead_letter: true });
  }
});

// Queue stats
app.get('/api/queues/:queue/stats', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const q = req.params.queue;
  const states = ['pending', 'processing', 'completed', 'failed'];
  const stats = {};
  for (const s of states) {
    const { count } = await supabase.schema('vortexq').from('jobs').select('*', { count: 'exact', head: true }).eq('api_key_id', r.id).eq('queue', q).eq('status', s);
    stats[s] = count || 0;
  }
  const { count: dlq } = await supabase.schema('vortexq').from('dead_letter').select('*', { count: 'exact', head: true }).eq('queue', q);
  res.json({ queue: q, stats, dead_letter_count: dlq || 0 });
});

const PORT = process.env.PORT || 3005;
app.listen(PORT, () => console.log(`🌀 VortexQ running on :${PORT}`));

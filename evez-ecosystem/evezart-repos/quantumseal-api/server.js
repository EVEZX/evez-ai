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
  const { data } = await supabase.schema('quantumseal').from('api_keys').select('*').eq('key_hash', h).eq('is_active', true).single();
  if (!data) return { r: null, e: { s: 403, b: { error: 'Invalid API key' } } };
  return { r: data, e: null };
}

app.get('/api/health', (_, res) => res.json({ status: 'operational', service: 'QuantumSeal Integrity Verification', version: '1.0.0', timestamp: new Date().toISOString() }));

app.post('/api/keys', async (req, res) => {
  const { name, email } = req.body || {};
  if (!name) return res.status(400).json({ error: 'name required' });
  const raw = `qs_${randomBytes(24).toString('hex')}`;
  const { data, error } = await supabase.schema('quantumseal').from('api_keys').insert({ key_hash: createHash('sha256').update(raw).digest('hex'), name, owner_email: email }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json({ api_key: raw, key_id: data.id, limits: { monthly_quota: 500 } });
});

// Seal content (create tamper-proof hash)
app.post('/api/seal', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { content, algorithm = 'sha256', metadata = {}, chain_to } = req.body || {};
  if (!content) return res.status(400).json({ error: 'content required' });
  const contentHash = createHash(algorithm).update(typeof content === 'string' ? content : JSON.stringify(content)).digest('hex');
  let sealChain = contentHash;
  let previousSealId = null;
  if (chain_to) {
    const { data: prev } = await supabase.schema('quantumseal').from('seals').select('id, seal_chain').eq('id', chain_to).single();
    if (prev) { previousSealId = prev.id; sealChain = createHash('sha256').update(prev.seal_chain + contentHash).digest('hex'); }
  }
  const { data, error } = await supabase.schema('quantumseal').from('seals').insert({ api_key_id: r.id, content_hash: contentHash, algorithm, metadata, seal_chain: sealChain, previous_seal_id: previousSealId }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json({ seal_id: data.id, content_hash: contentHash, seal_chain: sealChain, algorithm, chained_to: previousSealId, created_at: data.created_at, message: 'Content sealed. Use /api/verify to validate integrity.' });
});

// Verify content against seal
app.post('/api/verify', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { seal_id, content, content_hash } = req.body || {};
  if (!seal_id) return res.status(400).json({ error: 'seal_id required' });
  const { data: seal } = await supabase.schema('quantumseal').from('seals').select('*').eq('id', seal_id).single();
  if (!seal) return res.status(404).json({ error: 'Seal not found' });
  let computedHash = content_hash;
  if (!computedHash && content) computedHash = createHash(seal.algorithm).update(typeof content === 'string' ? content : JSON.stringify(content)).digest('hex');
  if (!computedHash) return res.status(400).json({ error: 'Provide content or content_hash' });
  const isValid = computedHash === seal.content_hash;
  await supabase.schema('quantumseal').from('verifications').insert({ seal_id: seal.id, is_valid: isValid, verifier_ip: req.ip });
  await supabase.schema('quantumseal').from('seals').update({ verified_count: seal.verified_count + 1, last_verified_at: new Date().toISOString() }).eq('id', seal.id);
  res.json({ seal_id, is_valid: isValid, algorithm: seal.algorithm, sealed_at: seal.created_at, verified_count: seal.verified_count + 1, chain_valid: isValid, metadata: seal.metadata });
});

// Get seal chain history
app.get('/api/chain/:seal_id', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const chain = [];
  let current = req.params.seal_id;
  while (current && chain.length < 100) {
    const { data } = await supabase.schema('quantumseal').from('seals').select('id, content_hash, seal_chain, algorithm, previous_seal_id, created_at, metadata').eq('id', current).single();
    if (!data) break;
    chain.push(data);
    current = data.previous_seal_id;
  }
  res.json({ chain_length: chain.length, seals: chain });
});

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => console.log(`🔐 QuantumSeal running on :${PORT}`));

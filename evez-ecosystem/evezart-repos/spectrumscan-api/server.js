import express from 'express';
import { createClient } from '@supabase/supabase-js';
import { createHash, randomBytes } from 'crypto';
import https from 'https';
import http from 'http';

const app = express();
app.use(express.json());
const supabase = createClient(process.env.SUPABASE_URL||'', process.env.SUPABASE_SERVICE_KEY||'');

const SECURITY_HEADERS = {
  'strict-transport-security': { weight: 15, label: 'HSTS', desc: 'Forces HTTPS connections' },
  'content-security-policy': { weight: 15, label: 'CSP', desc: 'Prevents XSS and injection attacks' },
  'x-content-type-options': { weight: 10, label: 'X-Content-Type-Options', desc: 'Prevents MIME sniffing' },
  'x-frame-options': { weight: 10, label: 'X-Frame-Options', desc: 'Prevents clickjacking' },
  'x-xss-protection': { weight: 5, label: 'X-XSS-Protection', desc: 'Legacy XSS filter' },
  'referrer-policy': { weight: 10, label: 'Referrer-Policy', desc: 'Controls referrer information' },
  'permissions-policy': { weight: 10, label: 'Permissions-Policy', desc: 'Controls browser features' },
  'cross-origin-opener-policy': { weight: 5, label: 'COOP', desc: 'Isolates browsing context' },
  'cross-origin-resource-policy': { weight: 5, label: 'CORP', desc: 'Controls cross-origin resource loading' },
  'cross-origin-embedder-policy': { weight: 5, label: 'COEP', desc: 'Controls cross-origin embedding' },
  'cache-control': { weight: 5, label: 'Cache-Control', desc: 'Controls caching behavior' },
  'x-permitted-cross-domain-policies': { weight: 5, label: 'X-Permitted-Cross-Domain', desc: 'Controls Flash/PDF cross-domain' }
};

async function auth(req) {
  const k = req.headers['x-api-key'];
  if (!k) return { r: null, e: { s: 401, b: { error: 'Missing x-api-key' } } };
  const h = createHash('sha256').update(k).digest('hex');
  const { data } = await supabase.schema('spectrumscan').from('api_keys').select('*').eq('key_hash', h).eq('is_active', true).single();
  if (!data) return { r: null, e: { s: 403, b: { error: 'Invalid API key' } } };
  return { r: data, e: null };
}

function gradeFromScore(s) { return s >= 90 ? 'A+' : s >= 80 ? 'A' : s >= 70 ? 'B' : s >= 60 ? 'C' : s >= 40 ? 'D' : 'F'; }

app.get('/api/health', (_, res) => res.json({ status: 'operational', service: 'SpectrumScan Security Scanner', version: '1.0.0', timestamp: new Date().toISOString() }));

app.post('/api/keys', async (req, res) => {
  const { name, email } = req.body || {};
  if (!name) return res.status(400).json({ error: 'name required' });
  const raw = `ss_${randomBytes(24).toString('hex')}`;
  const { data, error } = await supabase.schema('spectrumscan').from('api_keys').insert({ key_hash: createHash('sha256').update(raw).digest('hex'), name, owner_email: email }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json({ api_key: raw, key_id: data.id, limits: { monthly_scans: 200 } });
});

// Scan URL security headers
app.post('/api/scan', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { url } = req.body || {};
  if (!url) return res.status(400).json({ error: 'url required' });
  const urlHash = createHash('sha256').update(url).digest('hex');

  // Check cache
  const { data: cached } = await supabase.schema('spectrumscan').from('scan_cache').select('*').eq('url_hash', urlHash).gt('expires_at', new Date().toISOString()).single();
  if (cached) return res.json({ source: 'cache', ...cached.scan_result });

  const started = Date.now();
  try {
    const fr = await fetch(url, { method: 'HEAD', headers: { 'User-Agent': 'SpectrumScan/1.0' }, signal: AbortSignal.timeout(15000), redirect: 'follow' });
    const headers = Object.fromEntries([...fr.headers.entries()].map(([k,v]) => [k.toLowerCase(), v]));
    const present = [], missing = [], recommendations = [];
    let score = 0, maxScore = 0;

    for (const [header, info] of Object.entries(SECURITY_HEADERS)) {
      maxScore += info.weight;
      if (headers[header]) { present.push({ header: info.label, value: headers[header] }); score += info.weight; }
      else { missing.push({ header: info.label, description: info.desc }); recommendations.push({ action: `Add ${info.label} header`, description: info.desc, priority: info.weight >= 10 ? 'high' : 'medium' }); }
    }

    // Check for dangerous headers
    if (headers['server']) recommendations.push({ action: 'Remove Server header', description: 'Exposes server technology', priority: 'medium' });
    if (headers['x-powered-by']) recommendations.push({ action: 'Remove X-Powered-By header', description: 'Exposes technology stack', priority: 'high' });

    const finalScore = Math.round((score / maxScore) * 100);
    const grade = gradeFromScore(finalScore);
    const scanMs = Date.now() - started;

    const result = { url, grade, score: finalScore, headers_present: present, headers_missing: missing, dangerous_headers: ['server', 'x-powered-by'].filter(h => headers[h]).map(h => ({ header: h, value: headers[h] })), recommendations, scan_time_ms: scanMs, scanned_at: new Date().toISOString() };

    await supabase.schema('spectrumscan').from('scans').insert({ api_key_id: r.id, url, url_hash: urlHash, grade, score: finalScore, headers_present: present.map(p=>p.header), headers_missing: missing.map(m=>m.header), recommendations, scan_time_ms: scanMs });
    await supabase.schema('spectrumscan').from('scan_cache').upsert({ url_hash: urlHash, url, scan_result: result, cached_at: new Date().toISOString(), expires_at: new Date(Date.now() + 21600000).toISOString() }, { onConflict: 'url_hash' });

    res.json({ source: 'live', ...result });
  } catch (err) {
    res.status(500).json({ error: 'Scan failed', message: err.message, url });
  }
});

// Compare multiple URLs
app.post('/api/compare', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { urls } = req.body || {};
  if (!urls || !Array.isArray(urls) || urls.length < 2) return res.status(400).json({ error: 'Provide array of 2+ urls' });
  if (urls.length > 10) return res.status(400).json({ error: 'Max 10 URLs per comparison' });
  const results = [];
  for (const url of urls) {
    try {
      const fr = await fetch(url, { method: 'HEAD', headers: { 'User-Agent': 'SpectrumScan/1.0' }, signal: AbortSignal.timeout(10000) });
      const headers = Object.fromEntries([...fr.headers.entries()].map(([k,v]) => [k.toLowerCase(), v]));
      let score = 0, max = 0;
      for (const [h, info] of Object.entries(SECURITY_HEADERS)) { max += info.weight; if (headers[h]) score += info.weight; }
      const pct = Math.round((score/max)*100);
      results.push({ url, grade: gradeFromScore(pct), score: pct, status: fr.status });
    } catch { results.push({ url, grade: 'ERR', score: 0, status: 0, error: 'Unreachable' }); }
  }
  results.sort((a,b) => b.score - a.score);
  res.json({ comparison: results, best: results[0]?.url, worst: results[results.length-1]?.url });
});

const PORT = process.env.PORT || 3004;
app.listen(PORT, () => console.log(`🛡️ SpectrumScan running on :${PORT}`));

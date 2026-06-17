import express from 'express';
import { createClient } from '@supabase/supabase-js';
import { createHash, randomBytes } from 'crypto';

const app = express();
app.use(express.json());
const supabase = createClient(process.env.SUPABASE_URL||'', process.env.SUPABASE_SERVICE_KEY||'');

function genCode() { return randomBytes(4).toString('base64url').replace(/[^a-zA-Z0-9]/g, '').substring(0, 7); }

async function auth(req) {
  const k = req.headers['x-api-key'];
  if (!k) return { r: null, e: { s: 401, b: { error: 'Missing x-api-key' } } };
  const h = createHash('sha256').update(k).digest('hex');
  const { data } = await supabase.schema('nexuslink').from('api_keys').select('*').eq('key_hash', h).eq('is_active', true).single();
  if (!data) return { r: null, e: { s: 403, b: { error: 'Invalid API key' } } };
  return { r: data, e: null };
}

app.get('/api/health', (_, res) => res.json({ status: 'operational', service: 'NexusLink URL Shortener', version: '1.0.0', timestamp: new Date().toISOString() }));

app.post('/api/keys', async (req, res) => {
  const { name, email } = req.body || {};
  if (!name) return res.status(400).json({ error: 'name required' });
  const raw = `nl_${randomBytes(24).toString('hex')}`;
  const { data, error } = await supabase.schema('nexuslink').from('api_keys').insert({ key_hash: createHash('sha256').update(raw).digest('hex'), name, owner_email: email }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json({ api_key: raw, key_id: data.id, limits: { max_links: 100, monthly_clicks: 10000 } });
});

// Shorten URL
app.post('/api/links', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { url, title, tags = [], custom_code, expires_in_hours } = req.body || {};
  if (!url) return res.status(400).json({ error: 'url required' });
  const { count } = await supabase.schema('nexuslink').from('links').select('*', { count: 'exact', head: true }).eq('api_key_id', r.id);
  if (count >= r.max_links) return res.status(429).json({ error: 'Link limit reached' });
  const code = custom_code || genCode();
  const expires_at = expires_in_hours ? new Date(Date.now() + expires_in_hours * 3600000).toISOString() : null;
  const { data, error } = await supabase.schema('nexuslink').from('links').insert({ api_key_id: r.id, short_code: code, target_url: url, title, tags, expires_at }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.status(201).json({ short_code: code, short_url: `${req.protocol}://${req.get('host')}/r/${code}`, target_url: url, title, expires_at, created_at: data.created_at });
});

// Redirect
app.get('/r/:code', async (req, res) => {
  const { data: link } = await supabase.schema('nexuslink').from('links').select('*').eq('short_code', req.params.code).eq('is_active', true).single();
  if (!link) return res.status(404).json({ error: 'Link not found' });
  if (link.expires_at && new Date(link.expires_at) < new Date()) return res.status(410).json({ error: 'Link expired' });
  const ua = req.headers['user-agent'] || '';
  const device = /mobile/i.test(ua) ? 'mobile' : /tablet/i.test(ua) ? 'tablet' : 'desktop';
  const browser = /chrome/i.test(ua) ? 'chrome' : /firefox/i.test(ua) ? 'firefox' : /safari/i.test(ua) ? 'safari' : 'other';
  await supabase.schema('nexuslink').from('clicks').insert({ link_id: link.id, referrer: req.headers.referer, user_agent: ua, ip_hash: createHash('sha256').update(req.ip||'').digest('hex').substring(0,16), device_type: device, browser });
  await supabase.schema('nexuslink').from('links').update({ click_count: link.click_count + 1 }).eq('id', link.id);
  res.redirect(302, link.target_url);
});

// Analytics
app.get('/api/links/:code/analytics', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { data: link } = await supabase.schema('nexuslink').from('links').select('*').eq('short_code', req.params.code).eq('api_key_id', r.id).single();
  if (!link) return res.status(404).json({ error: 'Link not found' });
  const { data: clicks } = await supabase.schema('nexuslink').from('clicks').select('device_type, browser, referrer, clicked_at').eq('link_id', link.id).order('clicked_at', { ascending: false }).limit(100);
  const devices = {}, browsers = {}, referrers = {};
  (clicks||[]).forEach(c => { devices[c.device_type] = (devices[c.device_type]||0)+1; browsers[c.browser] = (browsers[c.browser]||0)+1; if (c.referrer) referrers[c.referrer] = (referrers[c.referrer]||0)+1; });
  res.json({ link: { short_code: link.short_code, target_url: link.target_url, total_clicks: link.click_count, created_at: link.created_at }, analytics: { devices, browsers, top_referrers: Object.entries(referrers).sort((a,b)=>b[1]-a[1]).slice(0,10).map(([r,c])=>({referrer:r,clicks:c})), recent_clicks: (clicks||[]).slice(0,20) } });
});

// List links
app.get('/api/links', async (req, res) => {
  const { r, e } = await auth(req);
  if (e) return res.status(e.s).json(e.b);
  const { data } = await supabase.schema('nexuslink').from('links').select('short_code, target_url, title, click_count, is_active, created_at').eq('api_key_id', r.id).order('created_at', { ascending: false });
  res.json({ links: data || [] });
});

const PORT = process.env.PORT || 3003;
app.listen(PORT, () => console.log(`🔗 NexusLink running on :${PORT}`));

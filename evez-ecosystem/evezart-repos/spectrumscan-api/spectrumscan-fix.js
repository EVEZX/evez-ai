// spectrumscan-fix.js — ESM
// Fixes: 546ms avg latency, 2.95% error rate, bad training data
// Updated: column names match evezstation.training_pairs schema

import https from 'https';
import http from 'http';

const SCAN_TIMEOUT_MS = 2000;
const MAX_URL_LENGTH  = 2048;
const MIN_QUALITY     = 0.6;

export const validateUrl = (raw) => {
  if (!raw) return { ok: false, reason: 'No URL provided' };
  if (raw.length > MAX_URL_LENGTH) return { ok: false, reason: 'URL too long' };
  try {
    const u = new URL(raw);
    if (!['http:', 'https:'].includes(u.protocol)) return { ok: false, reason: 'Only http/https allowed' };
    return { ok: true, url: u.href };
  } catch { return { ok: false, reason: 'Invalid URL format' }; }
};

export const fetchHeaders = (targetUrl) =>
  new Promise((resolve, reject) => {
    const u = new URL(targetUrl);
    const lib = u.protocol === 'https:' ? https : http;
    const start = Date.now();
    const req = lib.request(
      { method: 'HEAD', hostname: u.hostname, path: u.pathname || '/', timeout: SCAN_TIMEOUT_MS },
      (res) => {
        resolve({ statusCode: res.statusCode, headers: res.headers, latencyMs: Date.now() - start });
        res.resume();
      }
    );
    req.on('timeout', () => { req.destroy(); reject(Object.assign(new Error('Scan timed out'), { code: 'TIMEOUT' })); });
    req.on('error', (err) => reject(err));
    req.setTimeout(SCAN_TIMEOUT_MS);
    req.end();
  });

export const gradeHeaders = (headers = {}) => {
  const checks = [
    { name: 'Strict-Transport-Security', key: 'strict-transport-security', weight: 20 },
    { name: 'Content-Security-Policy',   key: 'content-security-policy',   weight: 25 },
    { name: 'X-Frame-Options',           key: 'x-frame-options',           weight: 15 },
    { name: 'X-Content-Type-Options',    key: 'x-content-type-options',    weight: 15 },
    { name: 'Referrer-Policy',           key: 'referrer-policy',           weight: 10 },
    { name: 'Permissions-Policy',        key: 'permissions-policy',        weight: 10 },
    { name: 'X-XSS-Protection',          key: 'x-xss-protection',          weight:  5 },
  ];
  let score = 0;
  const results = checks.map(c => {
    const present = !!headers[c.key];
    if (present) score += c.weight;
    return { header: c.name, present, value: headers[c.key] || null };
  });
  const grade = score >= 90 ? 'A+' : score >= 75 ? 'A' : score >= 60 ? 'B' : score >= 45 ? 'C' : score >= 30 ? 'D' : 'F';
  return { score, grade, results };
};

export const scoreForTraining = ({ latencyMs, grade, errorCode }) => {
  if (errorCode) return 0;
  if (latencyMs > SCAN_TIMEOUT_MS) return 0;
  const gradeScore = { 'A+': 1.0, A: 0.9, B: 0.8, C: 0.7, D: 0.6, F: 0.5 };
  const latencyPenalty = Math.min(latencyMs / 5000, 0.3);
  return Math.max(0, (gradeScore[grade] || 0.5) - latencyPenalty);
};

const logTrainingPair = async (supabase, { input, output, quality }) => {
  if (!supabase || quality < MIN_QUALITY) return;
  try {
    await supabase.schema('evezstation').from('training_pairs').insert({
      service:       'spectrumscan',
      endpoint:      '/scan',
      input_data:    input,
      output_data:   output,
      quality_score: quality,
      latency_ms:    output.latencyMs || 0,
      tokens_in:     JSON.stringify(input).length,
      tokens_out:    JSON.stringify(output).length,
      created_at:    new Date().toISOString()
    });
  } catch (err) {
    console.warn('[EVEZ TRAINING LOG]', err?.message);
  }
};

export const makeScanHandler = (supabase) => async (req, res) => {
  const start = Date.now();
  const raw = req.body?.url || req.query?.url;
  const validation = validateUrl(raw);
  if (!validation.ok) return res.status(400).json({ error: validation.reason });

  try {
    const { statusCode, headers, latencyMs } = await fetchHeaders(validation.url);
    const { score, grade, results } = gradeHeaders(headers);
    const output = { url: validation.url, statusCode, grade, score, latencyMs, headers: results, scannedAt: new Date().toISOString() };
    const quality = scoreForTraining({ latencyMs, grade });
    await logTrainingPair(supabase, { input: { url: validation.url }, output, quality });
    return res.json({ ok: true, ...output, totalMs: Date.now() - start });
  } catch (err) {
    const isTimeout = err.code === 'TIMEOUT';
    return res.status(isTimeout ? 408 : 502).json({
      ok: false, error: isTimeout ? 'Scan timed out (2s limit)' : 'Scan failed',
      code: err.code || 'SCAN_ERROR', url: validation.url, totalMs: Date.now() - start
    });
  }
};

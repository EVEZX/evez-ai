#!/usr/bin/env node
const urls = process.argv.slice(2);
const defaults = [process.env.OPENCLAW_URL || 'http://127.0.0.1:18789'];
const targets = urls.length ? urls : defaults;

for (const base of targets) {
  const url = base.replace(/\/$/, '') + '/healthz';
  try {
    const res = await fetch(url, { headers: process.env.OPENCLAW_AUTH_TOKEN ? { authorization: `Bearer ${process.env.OPENCLAW_AUTH_TOKEN}` } : {} });
    const text = await res.text();
    console.log(`${res.ok ? '✅' : '⚠️'} ${url} -> ${res.status} ${text.slice(0, 120)}`);
    if (!res.ok) process.exitCode = 1;
  } catch (err) {
    console.log(`❌ ${url} -> ${err.message}`);
    process.exitCode = 1;
  }
}

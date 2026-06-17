#!/usr/bin/env node
const BASE_URL = "https://evez-api2.fly.dev/v1";
const args = process.argv.slice(2);
const apiKey = process.env.EVEZ_API_KEY || args.find(a => a.startsWith('--key='))?.split('=')[1];
const model = args.find(a => a.startsWith('--model='))?.split('=')[1] || 'evez-smart';

if (!apiKey) {
  console.log('🧠 EVEZ AI CLI\n\nUsage: EVEZ_API_KEY=your-key evez "your prompt"\n       evez --key=your-key "your prompt"\n\nGet a free key: https://evez-api2.fly.dev/signup\nModels: evez-smart, evez-code, evez-fast, evez-vision');
  process.exit(1);
}

const prompt = args.filter(a => !a.startsWith('--')).join(' ');
if (!prompt) { console.log('Please provide a prompt'); process.exit(1); }

fetch(`${BASE_URL}/chat/completions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
  body: JSON.stringify({ model, messages: [{ role: 'user', content: prompt }] })
}).then(r => r.json()).then(d => {
  console.log(d.choices?.[0]?.message?.content || JSON.stringify(d));
}).catch(e => console.error('Error:', e.message));

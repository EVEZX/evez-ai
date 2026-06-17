const VULTR_BASE = 'https://api.vultrinference.com/v1';
const MODELS = {
  'evez-smart': 'zai-org/GLM-5.1-FP8',
  'evez-code': 'nvidia/DeepSeek-V3.2-NVFP4',
  'evez-fast': 'MiniMaxAI/MiniMax-M2.5',
  'evez-vision': 'moonshotai/Kimi-K2.5',
};

export default async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    return res.status(200).end();
  }
  
  const auth = req.headers.authorization?.replace('Bearer ', '');
  if (!auth || !auth.startsWith('evez-')) {
    return res.status(401).json({ error: { message: 'Invalid API key', type: 'auth_error' }});
  }

  const { model, messages, max_tokens, temperature } = req.body;
  const upstream = MODELS[model];
  if (!upstream) return res.status(400).json({ error: { message: `Unknown model: ${model}` }});

  const vultrKey = process.env.VULTR_API_KEY;
  const resp = await fetch(`${VULTR_BASE}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${vultrKey}` },
    body: JSON.stringify({ model: upstream, messages, max_tokens: max_tokens || 4096, temperature: temperature || 0.7 })
  });

  const data = await resp.json();
  data.model = model;
  res.setHeader('Access-Control-Allow-Origin', '*');
  return res.status(resp.status).json(data);
}

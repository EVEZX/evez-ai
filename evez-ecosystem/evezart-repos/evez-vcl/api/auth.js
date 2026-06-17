// api/auth.js — JWT auth: replace hardcoded tokens
import jwt from jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET;

const VALID_CREDENTIALS = {
  'evez-demo': { tier: 'demo', key: process.env.DEMO_ACCESS_KEY },
  'evez-pilot': { tier: 'pilot', key: process.env.PILOT_ACCESS_KEY },
  'evez-owner': { tier: 'owner', key: process.env.OWNER_ACCESS_KEY },
};

export default function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  
  const { username, key } = req.body || {};
  
  const cred = VALID_CREDENTIALS[username];
  if (!cred || cred.key !== key) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  
  const token = jwt.sign(
    { username, tier: cred.tier, iat: Date.now() },
    JWT_SECRET,
    { expiresIn: '24h' }
  );
  
  res.status(200).json({ token, tier: cred.tier, expires_in: 86400 });
}
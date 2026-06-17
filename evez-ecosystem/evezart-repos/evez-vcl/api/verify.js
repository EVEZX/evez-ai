// api/verify.js — Verify JWT token
import jwt from 'jsonwebtoken';

export default function handler(req, res) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'No token provided' });
  }
  
  try {
    const token = auth.replace('Bearer ', '');
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    res.status(200).json({ valid: true, tier: decoded.tier, username: decoded.username });
  } catch (err) {
    res.status(401).json({ valid: false, error: err.message });
  }
}
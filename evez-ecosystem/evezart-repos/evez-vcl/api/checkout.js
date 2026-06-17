// api/checkout.js — Stripe Checkout for EVEZ topology artifacts
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  
  const { artifact_id = 'fire-latest', tier = 'solo' } = req.body || {};
  
  const PRICES = {
    solo: { amount: 900, name: 'EVEZ Solo License — Cognition Artifact' },
    standard: { amount: 4900, name: 'EVEZ Solo License — Cognition Artifact' },
    studio: { amount: 19900, name: 'EVEZ Studio License' },
  };
  
  const price = PRICES[tier] || PRICES.solo;
  
  try {
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [{
        price_data: {
          currency: 'usd',
          product_data: {
            name: price.name,
            description: `Artifact ID: ${artifact_id}. Mathematical topology visualization of AI cognition. Powered by EVEZ Visual Cognition Layer.`,
          },
          unit_amount: price.amount,
        },
        quantity: 1,
      }],
      mode: 'payment',
      success_url: `https://evez-autonomizer.vercel.app/success?session_id={CHECKOUT_SESSION_ID}&artifact=${artifact_id}`,
      cancel_url: 'https://evez-autonomizer.vercel.app',
      metadata: { artifact_id, tier, source: 'evez-marketplace' },
    });
    
    res.status(200).json({ url: session.url, session_id: session.id });
  } catch (err) {
    console.error('Stripe error:', err);
    res.status(500).json({ error: err.message });
  }
}
// api/webhook.js — Stripe webhook: on successful payment
export const config = { api: { bodyParser: false } };
import Stripe from 'stripe';
import { buffer } from 'micro';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();
  const buf = await buffer(req);
  const sig = req.headers['stripe-signature'];
  let event;
  try {
    event = stripe.webhooks.constructEvent(buf, sig, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }
  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;
    const { artifact_id, tier } = session.metadata;
    const customerEmail = session.customer_details?.email;
    const licenseToken = `evez-${tier}-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
    console.log(`License issued: ${licenseToken} for ${customerEmail}`);
  }
  res.status(200).json({ received: true });
}
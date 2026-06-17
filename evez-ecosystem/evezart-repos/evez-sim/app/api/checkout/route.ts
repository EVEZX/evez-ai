import { NextResponse } from 'next/server'

// EVEZ-SIM Stripe Checkout
// Creates a one-time $5 payment session for /agent access
// Requires STRIPE_SECRET_KEY env var on Vercel
// Add at: vercel.com/evez666/evez-sim/settings/environment-variables

const PRICE_USD = 500 // $5.00 in cents
const PRODUCT_NAME = 'EVEZ-OS Agent Field Access'
const PRODUCT_DESC = 'One-time access: live agentic circuit field. Circuits are real AI processes. You\'re watching EVEZ-OS think.'

export async function POST(req: Request) {
  const stripeKey = process.env.STRIPE_SECRET_KEY
  
  if (!stripeKey) {
    // Stripe not configured — return demo mode signal
    return NextResponse.json({ demo: true, url: null, message: 'Stripe not configured' }, { status: 200 })
  }

  try {
    const body = await req.json() as { origin?: string }
    const origin = body?.origin || 'https://evez-sim.vercel.app'
    
    const stripeRes = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${stripeKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        'mode': 'payment',
        'line_items[0][price_data][currency]': 'usd',
        'line_items[0][price_data][product_data][name]': PRODUCT_NAME,
        'line_items[0][price_data][product_data][description]': PRODUCT_DESC,
        'line_items[0][price_data][unit_amount]': String(PRICE_USD),
        'line_items[0][quantity]': '1',
        'success_url': `${origin}/agent?paid=1`,
        'cancel_url': `${origin}/agent`,
        'metadata[product]': 'evez-agent-access',
      }).toString()
    })
    
    const session = await stripeRes.json() as { url?: string; error?: { message: string } }
    
    if (!stripeRes.ok || session.error) {
      return NextResponse.json({ error: session.error?.message || 'Stripe error' }, { status: 400 })
    }
    
    return NextResponse.json({ url: session.url, demo: false })
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}

export async function GET() {
  const configured = !!process.env.STRIPE_SECRET_KEY
  return NextResponse.json({ configured, price_usd: PRICE_USD / 100 })
}
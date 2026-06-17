"""
api/stripe-webhook.py -- EVEZ-OS Stripe Webhook Handler
Vercel serverless function at POST /api/stripe-webhook
"""
import json, os, hashlib, hmac, time
from http.server import BaseHTTPRequestHandler

def verify_stripe_signature(payload, sig_header, secret):
    try:
        elements = {k: v for k, v in (x.split('=', 1) for x in sig_header.split(','))}
        timestamp = int(elements.get('t', '0'))
        signatures = [v for k, v in elements.items() if k == 'v1']
        if abs(time.time() - timestamp) > 300: return False
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(expected, sig) for sig in signatures)
    except: return False

def handle_event(event):
    etype = event.get('type', '')
    data = event.get('data', {}).get('object', {})
    if etype == 'checkout.session.completed':
        return {'action': 'checkout_complete', 'session_id': data.get('id'), 'amount_total': data.get('amount_total')}
    elif etype == 'payment_intent.succeeded':
        return {'action': 'payment_succeeded', 'payment_intent': data.get('id'), 'amount': data.get('amount')}
    elif etype == 'payment_intent.payment_failed':
        return {'action': 'payment_failed', 'payment_intent': data.get('id')}
    elif etype in ('customer.subscription.created', 'customer.subscription.deleted'):
        return {'action': etype.replace('.','_'), 'subscription_id': data.get('id'), 'status': data.get('status')}
    elif etype == 'issuing_authorization.request':
        return {'action': 'issuing_authorize', 'authorization_id': data.get('id'), 'amount': data.get('amount'), 'approved': True}
    elif etype == 'issuing_transaction.created':
        return {'action': 'issuing_transaction', 'transaction_id': data.get('id'), 'amount': data.get('amount')}
    return {'action': 'unhandled', 'type': etype}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        content_length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(content_length)
        sig_header = self.headers.get('Stripe-Signature', '')
        if webhook_secret and not verify_stripe_signature(payload, sig_header, webhook_secret):
            self.send_response(400); self.end_headers(); self.wfile.write(b'Invalid signature'); return
        try: event = json.loads(payload)
        except json.JSONDecodeError:
            self.send_response(400); self.end_headers(); self.wfile.write(b'Invalid JSON'); return
        result = handle_event(event)
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
        self.wfile.write(json.dumps({'received': True, 'result': result}).encode())
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok', 'endpoint': 'stripe-webhook'}).encode())
    def log_message(self, *args): pass

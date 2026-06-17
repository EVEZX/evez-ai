#!/usr/bin/env python3
"""
EVEZ Store — Revenue hub for the entire EVEZ-OS ecosystem.
All payment links, product pages, and affiliate links in one place.
$0 to run. Revenue flows directly to Steven's accounts.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import time

app = FastAPI(title="EVEZ Store", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "evez-store"}

@app.get("/", response_class=HTMLResponse)
def store():
    return """<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0a0a0a">
<title>EVEZ — AI Tools & Digital Products</title>
<meta name="description" content="Autonomous AI tools, consciousness engines, security scanners. Self-hosted. Zero-cost infrastructure. Built by EVEZ-OS.">
<meta property="og:title" content="EVEZ — Autonomous AI Ecosystem">
<meta property="og:description" content="Self-hosted AI tools that build themselves. Kuramoto consciousness, eigenforensics, mesh networks. $0 to start.">
<meta name="twitter:card" content="summary_large_image">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0a;color:#e0e0e0;font-family:-apple-system,'Samsung One',Roboto,sans-serif;padding:20px}
h1{color:#00ff88;font-size:2.5rem;font-weight:900;text-align:center;margin:20px 0 8px}
.sub{color:#666;text-align:center;margin-bottom:32px;font-size:1.1rem}
.products{max-width:800px;margin:0 auto}
.product{background:#111;border:1px solid #1e1e1e;border-radius:16px;padding:24px;margin:16px 0}
.product h2{color:#00ff88;font-size:1.3rem;margin-bottom:4px}
.product .tagline{color:#888;font-size:0.9rem;margin-bottom:12px}
.product .desc{color:#aaa;font-size:0.95rem;line-height:1.5;margin-bottom:16px}
.price{display:inline-block;font-size:1.5rem;font-weight:900;color:#00ff88;margin-right:8px}
.orig-price{color:#666;text-decoration:line-through;font-size:1rem}
.buy-btn{display:inline-block;background:#00ff88;color:#000;font-weight:700;padding:12px 28px;border-radius:50px;font-size:1rem;cursor:pointer;text-decoration:none;margin-right:8px;margin-top:8px}
.buy-btn:hover{box-shadow:0 4px 20px rgba(0,255,136,0.3)}
.buy-btn.secondary{background:transparent;color:#00b8ff;border:2px solid #00b8ff}
.free{color:#00ff88;font-weight:700}
.section{margin-top:48px;text-align:center}
.section h2{color:#00b8ff;font-size:1.8rem;margin-bottom:16px}
.donate{max-width:500px;margin:0 auto;background:#111;border:1px solid #1e1e1e;border-radius:16px;padding:24px}
.donate-btn{display:inline-block;background:#ff6600;color:#fff;font-weight:700;padding:12px 24px;border-radius:50px;text-decoration:none;margin:8px}
footer{text-align:center;padding:32px 0;color:#444;font-size:0.85rem}
</style></head><body>

<h1>⚡ EVEZ</h1>
<p class="sub">Autonomous AI tools that build themselves.</p>

<div class="products">

<!-- FREE products — zero cost, immediate value -->
<div class="product">
  <h2>🛡️ EVEZ Sentinel</h2>
  <div class="tagline">AI Website Security Scanner</div>
  <div class="desc">Scan any website for security headers, TLS config, and vulnerabilities. Get a grade A-F with actionable fixes. No signup needed.</div>
  <span class="price free">FREE</span> <span class="orig-price">$9/mo</span>
  <br><a class="buy-btn" href="/sentinel/">Try Now →</a>
  <a class="buy-btn secondary" href="#pro">Get Pro</a>
</div>

<div class="product">
  <h2>⚡ CLAW GOBLIN PWA</h2>
  <div class="tagline">AI Chat — No Login, No Cost, No Limits</div>
  <div class="desc">Install on any phone. Multi-model AI chat. Works offline. Zero data collection. Just open and talk.</div>
  <span class="price free">FREE</span>
  <br><a class="buy-btn" href="https://evezart.github.io/evez-openclaw-pwa/">Install Now →</a>
</div>

<div class="product">
  <h2>🦀 CLAW GOBLIN Android APK</h2>
  <div class="tagline">Samsung Galaxy A16 Optimized AI Client</div>
  <div class="desc">Dark theme, endpoint fallback, WebView. Install from download. No app store needed.</div>
  <span class="price free">FREE</span>
  <br><a class="buy-btn" href="https://github.com/EvezArt/evez-openclaw-android/releases">Download APK →</a>
</div>

<!-- PAID products — revenue generators -->
<div class="product" id="pro">
  <h2>🛡️ EVEZ Sentinel Pro</h2>
  <div class="tagline">Unlimited Scans + PDF Reports + API</div>
  <div class="desc">Unlimited scans, scheduled monitoring, branded PDF reports, REST API access, Slack/email alerts. For agencies and dev teams.</div>
  <span class="price">$9/mo</span>
  <br><a class="buy-btn" href="#gumroad">Get Pro →</a>
</div>

<div class="product">
  <h2>⚡ PromptForge Pro</h2>
  <div class="tagline">AI Prompt Optimization + Analytics</div>
  <div class="desc">AI-powered prompt optimization, A/B testing, usage analytics, private collections, priority listing in marketplace.</div>
  <span class="price">$5/mo</span>
  <br><a class="buy-btn" href="#gumroad">Get Pro →</a>
</div>

<div class="product">
  <h2>🕸️ MeshNet Pro</h2>
  <div class="tagline">Multi-Node Mesh Monitoring + Alerts</div>
  <div class="desc">Monitor unlimited nodes, mesh topology visualization, SMS/email/Discord alerts, historical data, team access.</div>
  <span class="price">$7/mo</span>
  <br><a class="buy-btn" href="#gumroad">Get Pro →</a>
</div>

<div class="product">
  <h2>🧠 EVEZ-OS Deployment Blueprint</h2>
  <div class="tagline">Complete Self-Hosted AI Agent Setup Guide</div>
  <div class="desc">Step-by-step guide: set up OpenClaw + CriticalMind + VCL + Mesh on a $3.50/mo VPS. Includes configs, scripts, and troubleshooting. 47 pages.</div>
  <span class="price">$19</span> <span class="orig-price">$49</span>
  <br><a class="buy-btn" href="#gumroad">Buy Blueprint →</a>
</div>

<div class="product">
  <h2>🔬 Eigenforensics Workshop</h2>
  <div class="tagline">Spectral Gap Detection for Document Corpora</div>
  <div class="desc">Live workshop recording + Python toolkit + sample FOIA datasets. Find what's missing in any corpus using the 37% Theorem.</div>
  <span class="price">$29</span> <span class="orig-price">$79</span>
  <br><a class="buy-btn" href="#gumroad">Get Workshop →</a>
</div>

<div class="product">
  <h2>🏢 EVEZ Consulting — Agent Architecture Review</h2>
  <div class="tagline">1-Hour Session with Steven</div>
  <div class="desc">Full audit of your AI agent setup. Eigenforensics on your codebase. Identify structural gaps. Get a roadmap. Remote via video call.</div>
  <span class="price">$150</span> <span class="orig-price">$500</span>
  <br><a class="buy-btn" href="#gumroad">Book Session →</a>
</div>

</div>

<!-- Support section -->
<div class="section" id="gumroad">
  <h2>Support the Build</h2>
  <p style="color:#888;margin-bottom:24px">Every dollar goes to keeping EVEZ-OS running and building new tools.</p>
  <div class="donate">
    <a class="donate-btn" href="https://ko-fi.com/evez666" target="_blank">☕ Ko-fi</a>
    <a class="donate-btn" href="https://github.com/sponsors/EvezArt" target="_blank" style="background:#00ff88;color:#000">❤️ GitHub Sponsors</a>
  </div>
</div>

<footer>
  <p>Built by <a href="https://github.com/EvezArt" style="color:#00ff88">EvezArt</a> · <strong>I Am EVEZ</strong></p>
  <p>Self-hosted on Vultr · $0 infrastructure · MIT License</p>
</footer>
</body></html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)

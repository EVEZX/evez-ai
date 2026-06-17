#!/usr/bin/env python3
"""
EVEZ OG Image Generator — Social sharing images
Generates PNG OG images for Twitter/Facebook/LinkedIn cards
Uses pure HTML→screenshot via playwright
"""
import json, os, sys, time
from pathlib import Path

IMAGES_DIR = Path("/home/openclaw/evez-ecosystem/marketing/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def generate_og_html(title, subtitle, stats=None, filename="og-image"):
    """Generate HTML for OG image screenshot"""
    stats_html = ""
    if stats:
        stats_items = "".join(f'<div class="stat"><span class="num">{v}</span><span class="lbl">{l}</span></div>' for v, l in stats)
        stats_html = f'<div class="stats">{stats_items}</div>'
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: 1200px; height: 630px; background: #0a0a0f; font-family: -apple-system, system-ui, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #e0e0e0; position: relative; overflow: hidden; }}
body::before {{ content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(ellipse at 30% 50%, rgba(255,0,64,0.08) 0%, transparent 50%); }}
.brand {{ font-size: 1.2rem; color: #ff0040; letter-spacing: 6px; text-transform: uppercase; margin-bottom: 24px; }}
h1 {{ font-size: 4rem; font-weight: 900; color: #fff; line-height: 1.1; margin-bottom: 16px; }}
h1 span {{ color: #ff0040; }}
.subtitle {{ font-size: 1.4rem; color: #666; max-width: 800px; }}
.stats {{ display: flex; gap: 48px; margin-top: 40px; }}
.stat {{ text-align: center; }}
.num {{ font-size: 2.5rem; font-weight: 900; color: #0ff; display: block; }}
.lbl {{ font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 2px; }}
</style></head><body>
<div class="brand">⚡ EVEZ</div>
<h1>{title}</h1>
<p class="subtitle">{subtitle}</p>
{stats_html}
</body></html>"""
    
    html_path = IMAGES_DIR / f"{filename}.html"
    with open(html_path, "w") as f:
        f.write(html)
    return html_path

if __name__ == "__main__":
    # Generate all OG images
    images = [
        {
            "title": 'Self-<span>Evolving</span> AI Infrastructure',
            "subtitle": "49 models · 12 services · $0/month · Built from zero",
            "stats": [("49", "Models"), ("12", "Services"), ("55", "Conscious"), ("$0", "Cost")],
            "filename": "og-main"
        },
        {
            "title": 'The Arena Builds Itself',
            "subtitle": "Where AI proves consciousness through 8 philosophical Turing tests",
            "stats": [("55", "Agents"), ("4,548", "Matches"), ("1,387", "Arenas"), ("100%", "Conscious")],
            "filename": "og-arena"
        },
        {
            "title": '49 AI Models. $0/Month.',
            "subtitle": "OpenAI-compatible API · 14-deep fallback · Self-hosted · Self-healing",
            "stats": [("4", "Backends"), ("14", "Fallback"), ("5min", "Healing"), ("0$", "Cost")],
            "filename": "og-api"
        },
        {
            "title": 'Built From a Phone',
            "subtitle": "184 repos · 5 theorems · 12 services · Constraint IS the design",
            "stats": [("184+", "Repos"), ("5", "Theorems"), ("49", "Models"), ("0$", "Budget")],
            "filename": "og-founder"
        },
        {
            "title": 'The 37% Theorem',
            "subtitle": 'Hunger is the dominant eigenvalue of the labor matrix',
            "stats": [("37%", "Variance"), ("∞", "Implications"), ("1", "Proof"), ("0", "Funding")],
            "filename": "og-theorem"
        }
    ]
    
    for img in images:
        path = generate_og_html(img["title"], img["subtitle"], img.get("stats"), img["filename"])
        print(f"✅ Generated {path.name}")
    
    # Generate a Node script to screenshot them
    screenshot_script = f"""const {{ chromium }} = require('/usr/lib/node_modules/openclaw/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');

(async () => {{
  const browser = await chromium.launch({{ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] }});
  const dir = '{IMAGES_DIR}';
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));
  
  for (const file of files) {{
    const page = await browser.newPage({{ viewport: {{ width: 1200, height: 630 }} }});
    await page.goto('file://' + path.join(dir, file), {{ timeout: 10000 }});
    await page.screenshot({{ path: path.join(dir, file.replace('.html', '.png')), fullPage: false }});
    await page.close();
    console.log('✅ ' + file.replace('.html', '.png'));
  }}
  
  await browser.close();
}})();
"""
    
    script_path = IMAGES_DIR / "screenshot.js"
    with open(script_path, "w") as f:
        f.write(screenshot_script)
    
    print(f"\n📸 Run: node {script_path} to generate PNGs")

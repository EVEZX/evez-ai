"""
Meme factory for disclosure.tools
Auto-generates shareable visuals when gap analysis detects structural incompleteness.
"""
import json
import hashlib
import time
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MemeTemplate:
    """A meme template with top/bottom text slots."""
    id: str
    name: str
    top_text: str
    bottom_text: str
    style: str  # "impact", "modern", "retro", "official"
    bg_color: str = "#1a1a2e"
    text_color: str = "#ffffff"


# Pre-built meme templates for UAP/FOIA context
MEME_TEMPLATES = {
    "redacted": MemeTemplate(
        id="redacted", name="Heavy Redaction",
        top_text="WHEN THE FOIA RELEASE IS",
        bottom_text="90% [REDACTED]",
        style="impact",
    ),
    "missing_records": MemeTemplate(
        id="missing_records", name="Missing Records",
        top_text="THE RECORDS ARE IN ANOTHER CASTLE",
        bottom_text="— AARO, probably",
        style="retro",
    ),
    "eigenvalue": MemeTemplate(
        id="eigenvalue", name="Negative Eigenvalue",
        top_text="THE EIGENVALUES DON'T LIE",
        bottom_text="BUT THE PENTAGON DOES",
        style="modern",
    ),
    "gap_detected": MemeTemplate(
        id="gap_detected", name="Gap Detected",
        top_text="I FIND YOUR LACK OF RECORDS",
        bottom_text="DISTURBING",
        style="impact",
    ),
    "37pct": MemeTemplate(
        id="37pct", name="37% Theorem",
        top_text="37% OF THE TENSION IS JUST",
        bottom_text="ONE MISSING DOCUMENT",
        style="modern",
    ),
    "classification": MemeTemplate(
        id="classification", name="Classification Shadow",
        top_text="YOU CAN REDACT THE TEXT",
        bottom_text="BUT YOU CAN'T REDACT THE MATH",
        style="impact",
    ),
    "phi": MemeTemplate(
        id="phi", name="Phi Too Low",
        top_text="Φ = 0.03",
        bottom_text="EVEN THE UNIVERSE KNOWS YOU'RE HIDING SOMETHING",
        style="modern",
    ),
    "foia": MemeTemplate(
        id="foia", name="FOIA Response",
        top_text="FOIA RESPONSE: WE FOUND 10,000 PAGES",
        bottom_text="9,999 ARE BLANK",
        style="retro",
    ),
}


@dataclass
class MemeImage:
    """Generated meme image data."""
    meme_id: str
    caption: str
    template_id: str
    gap_finding: str
    svg_content: str
    html_content: str
    created_at: int

    def to_dict(self) -> Dict:
        return {
            "meme_id": self.meme_id,
            "caption": self.caption,
            "template_id": self.template_id,
            "gap_finding": self.gap_finding,
            "created_at": self.created_at,
        }


def _generate_svg_meme(template: MemeTemplate, top_override: str = "",
                        bottom_override: str = "", caption: str = "") -> str:
    """Generate an SVG meme image."""
    top = top_override or template.top_text
    bottom = bottom_override or template.bottom_text

    if template.style == "impact":
        font_family = "Impact, Arial Black, sans-serif"
        font_size_top = "28px"
        font_size_bottom = "24px"
        stroke = '#000000'
        stroke_width = "2"
    elif template.style == "modern":
        font_family = "Inter, Helvetica, Arial, sans-serif"
        font_size_top = "22px"
        font_size_bottom = "20px"
        stroke = 'none'
        stroke_width = "0"
    else:  # retro
        font_family = "Courier New, monospace"
        font_size_top = "20px"
        font_size_bottom = "18px"
        stroke = 'none'
        stroke_width = "0"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="500" viewBox="0 0 600 500">
  <!-- Background -->
  <rect width="600" height="500" fill="{template.bg_color}"/>
  
  <!-- Disclosure.tools branding -->
  <text x="300" y="30" font-family="Courier New, monospace" font-size="10" fill="#666666" text-anchor="middle">disclosure.tools — eigenforensics meme</text>
  
  <!-- Top text -->
  <text x="300" y="120" font-family="{font_family}" font-size="{font_size_top}" fill="{template.text_color}" text-anchor="middle" stroke="{stroke}" stroke-width="{stroke_width}">
    <tspan x="300" dy="0">{top[:40]}</tspan>
    <tspan x="300" dy="35">{top[40:80]}</tspan>
  </text>
  
  <!-- Center graphic -->
  <g transform="translate(300,250)">
    <!-- Gap visualization -->
    <circle r="60" fill="none" stroke="#ff4444" stroke-width="3" opacity="0.8"/>
    <circle r="40" fill="none" stroke="#ff6666" stroke-width="2" opacity="0.6"/>
    <circle r="20" fill="none" stroke="#ff8888" stroke-width="1" opacity="0.4"/>
    <line x1="-80" y1="0" x2="80" y2="0" stroke="#ff4444" stroke-width="1" opacity="0.3"/>
    <line x1="0" y1="-80" x2="0" y2="80" stroke="#ff4444" stroke-width="1" opacity="0.3"/>
    <text y="5" font-family="Courier New, monospace" font-size="14" fill="#ff4444" text-anchor="middle">GAP</text>
  </g>
  
  <!-- Bottom text -->
  <text x="300" y="400" font-family="{font_family}" font-size="{font_size_bottom}" fill="{template.text_color}" text-anchor="middle" stroke="{stroke}" stroke-width="{stroke_width}">
    <tspan x="300" dy="0">{bottom[:45]}</tspan>
    <tspan x="300" dy="32">{bottom[45:90]}</tspan>
  </text>
  
  <!-- Footer -->
  <text x="300" y="470" font-family="Courier New, monospace" font-size="9" fill="#444444" text-anchor="middle">🔬 eigenforensics · η* ≈ 0.03 · disclosure.tools</text>
  <text x="300" y="485" font-family="Courier New, monospace" font-size="8" fill="#333333" text-anchor="middle">built by EVEZ666</text>
</svg>'''


def _generate_html_meme(template: MemeTemplate, top_override: str = "",
                         bottom_override: str = "", caption: str = "") -> str:
    """Generate a standalone HTML meme page."""
    top = top_override or template.top_text
    bottom = bottom_override or template.bottom_text

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>disclosure.tools meme</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: {template.bg_color}; color: {template.text_color}; font-family: system-ui; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
  .meme {{ width: 600px; padding: 40px; text-align: center; }}
  .meme-top {{ font-size: 28px; font-weight: 900; margin-bottom: 40px; line-height: 1.3; }}
  .meme-center {{ font-size: 80px; margin: 20px 0; opacity: 0.8; }}
  .meme-bottom {{ font-size: 24px; font-weight: 700; margin-top: 40px; line-height: 1.3; }}
  .meme-caption {{ font-size: 12px; color: #666; margin-top: 20px; font-family: monospace; }}
  .brand {{ font-size: 10px; color: #444; margin-top: 10px; font-family: monospace; }}
</style>
</head>
<body>
<div class="meme">
  <div class="meme-top">{top}</div>
  <div class="meme-center">🕳️</div>
  <div class="meme-bottom">{bottom}</div>
  <div class="meme-caption">{caption}</div>
  <div class="brand">disclosure.tools · eigenforensics · η* ≈ 0.03</div>
</div>
</body>
</html>'''


def generate_meme(
    caption: str,
    template_id: str = "gap_detected",
    top_override: str = "",
    bottom_override: str = "",
    gap_finding: str = "",
) -> MemeImage:
    """Generate a meme image from a gap finding caption."""
    template = MEME_TEMPLATES.get(template_id, MEME_TEMPLATES["gap_detected"])

    meme_id = f"MEME-{hashlib.sha256(f'{caption}{time.time()}'.encode()).hexdigest()[:8].upper()}"

    svg = _generate_svg_meme(template, top_override, bottom_override, caption)
    html = _generate_html_meme(template, top_override, bottom_override, caption)

    return MemeImage(
        meme_id=meme_id,
        caption=caption,
        template_id=template_id,
        gap_finding=gap_finding,
        svg_content=svg,
        html_content=html,
        created_at=int(time.time()),
    )


def auto_generate_memes(findings: List[Dict]) -> List[MemeImage]:
    """Auto-generate memes from gap findings (triggered by high/critical severity)."""
    memes = []

    # Template mapping by category
    category_templates = {
        "redaction": "redacted",
        "missing_record": "missing_records",
        "classification_shadow": "classification",
        "broken_chain": "gap_detected",
        "cross_ref_failure": "foia",
        "temporal_gap": "37pct",
    }

    for finding in findings:
        severity = finding.get("severity", "low")
        if severity not in ("high", "critical"):
            continue

        category = finding.get("category", "broken_chain")
        template_id = category_templates.get(category, "gap_detected")
        caption = finding.get("meme_caption", finding.get("description", "Gap detected"))

        meme = generate_meme(
            caption=caption,
            template_id=template_id,
            gap_finding=finding.get("description", ""),
        )
        memes.append(meme)

    return memes


def get_all_templates() -> Dict[str, Dict]:
    """Return all available meme templates."""
    return {tid: {"id": t.id, "name": t.name, "style": t.style}
            for tid, t in MEME_TEMPLATES.items()}

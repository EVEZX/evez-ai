"""
EVEZ Generative SVG Art - Math becomes visible
"""
import json, math, hashlib
from pathlib import Path

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

def eigenvalue_mandala(eigenvalues, name="eigenvalue_mandala"):
    n_rings = len(eigenvalues)
    size = 1000
    cx, cy = size / 2, size / 2
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">']
    svg.append(f'<rect width="{size}" height="{size}" fill="#050510"/>')
    svg.append(f'<defs><filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    for ring_idx, ev in enumerate(eigenvalues):
        ring_r = 80 + ring_idx * 70
        n_petals = max(3, int(abs(ev) * 10) + 3)
        rotation = ev * 30
        if ev < -0.5: color, opacity = "#ff3232", 0.9
        elif ev < 0: color, opacity = "#ff8832", 0.7
        elif ev < 0.5: color, opacity = "#32ff88", 0.6
        else: color, opacity = "#32aaff", 0.5
        group = f'<g transform="rotate({rotation} {cx} {cy})" filter="url(#glow)">'
        for petal in range(n_petals):
            angle = (petal / n_petals) * 360
            if ev < 0:
                r1 = ring_r
                r2 = ring_r - abs(ev) * 60
                x1 = cx + r1 * math.cos(math.radians(angle))
                y1 = cy + r1 * math.sin(math.radians(angle))
                x2 = cx + r2 * math.cos(math.radians(angle + 360 / n_petals / 2))
                y2 = cy + r2 * math.sin(math.radians(angle + 360 / n_petals / 2))
            else:
                r1 = ring_r
                r2 = ring_r + ev * 40
                x1 = cx + r1 * math.cos(math.radians(angle))
                y1 = cy + r1 * math.sin(math.radians(angle))
                x2 = cx + r2 * math.cos(math.radians(angle + 360 / n_petals / 2))
                y2 = cy + r2 * math.sin(math.radians(angle + 360 / n_petals / 2))
            cpx = cx + (r1 + r2) / 2 * math.cos(math.radians((angle + angle + 360 / n_petals / 2) / 2))
            cpy = cy + (r1 + r2) / 2 * math.sin(math.radians((angle + angle + 360 / n_petals / 2) / 2))
            group += f'<path d="M{cx},{cy} Q{cpx:.1f},{cpy:.1f} {x1:.1f},{y1:.1f}" stroke="{color}" stroke-width="1.5" fill="none" opacity="{opacity}"/>'
            group += f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="3" fill="{color}" opacity="{opacity}"/>'
            if ev < 0:
                group += f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="2" fill="{color}" opacity="{opacity * 0.7}"/>'
        group += f'<circle cx="{cx}" cy="{cy}" r="{ring_r}" stroke="{color}" stroke-width="0.5" fill="none" opacity="0.3"/>'
        group += '</g>'
        svg.append(group)
    svg.append('</svg>')
    path = OUT / f"{name}.svg"
    path.write_text('\n'.join(svg))
    print(f"  Madala {name}.svg ({n_rings} rings)")

def spine_labyrinth(events, name="spine_labyrinth"):
    size = 1000
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">']
    svg.append(f'<rect width="{size}" height="{size}" fill="#050508"/>')
    for i, event in enumerate(events):
        raw = json.dumps(event, sort_keys=True, default=str).encode()
        h = hashlib.sha256(raw).hexdigest()
        x = int(h[:3], 16) / 0xFFF * size
        y = int(h[3:6], 16) / 0xFFF * size
        angle = int(h[6:9], 16) / 0xFFF * 360
        length = 20 + int(h[9:12], 16) / 0xFFF * 80
        hue = (i * 37) % 360
        color = f"hsl({hue}, 70%, 50%)"
        x2 = x + length * math.cos(math.radians(angle))
        y2 = y + length * math.sin(math.radians(angle))
        svg.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="2" opacity="0.7"/>')
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
        if i > 0:
            prev_raw = json.dumps(events[i-1], sort_keys=True, default=str).encode()
            ph = hashlib.sha256(prev_raw).hexdigest()
            px = int(ph[:3], 16) / 0xFFF * size
            py = int(ph[3:6], 16) / 0xFFF * size
            svg.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#ffffff" stroke-width="0.5" opacity="0.2"/>')
    svg.append('</svg>')
    path = OUT / f"{name}.svg"
    path.write_text('\n'.join(svg))
    print(f"  Labyrinth {name}.svg ({len(events)} events)")

if __name__ == "__main__":
    print("Generative SVG art...\n")
    noclip_eigenvalues = [2.7044, 1.2799, 1.0593, 0.2838, 0.1014, -0.8838]
    eigenvalue_mandala(noclip_eigenvalues)
    eigenvalue_mandala(noclip_eigenvalues, "consciousness_mandala")
    try:
        with open("/home/openclaw/.openclaw/workspace/evez-repos/evez-revenue-bridge/revenue_spine.json") as f:
            spine_data = json.load(f)
        spine_labyrinth(spine_data.get("events", []))
    except: pass
    print("Done")

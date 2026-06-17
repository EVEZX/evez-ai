"""
EVEZ Media Factory — Generates media from system data in novel ways
Each generator transforms internal state into visual/audio artifacts
"""
import json, math, time, os, hashlib
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

# ─── 1. SPECTRAL LANDSCAPE ────────────────────────────────────────────────
def spectral_landscape(eigenvalues, name="spectral_landscape"):
    """Render eigenvalues as a 3D-like terrain where negative = canyons, positive = peaks"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (5, 8, 15))
    draw = ImageDraw.Draw(img)
    
    n = len(eigenvalues)
    # Map eigenvalues to landscape heights
    for x in range(W):
        # Interpolate across the eigenvalue spectrum
        t = x / W * (n - 1)
        idx = int(t)
        frac = t - idx
        if idx < n - 1:
            val = eigenvalues[idx] * (1 - frac) + eigenvalues[idx + 1] * frac
        else:
            val = eigenvalues[-1]
        
        # Height mapping: negative = down (canyons), positive = up (peaks)
        center_y = H * 0.5
        height = val * H * 0.15  # Scale factor
        
        y_top = int(center_y - max(height, 0))
        y_bot = int(center_y - min(height, 0))
        y_center = int(center_y)
        
        # Color based on eigenvalue sign
        if val < -0.5:
            # Deep canyon - hot red/orange
            intensity = min(255, int(abs(val) * 200))
            for y in range(min(y_center, y_bot), max(y_center, y_bot) + 1):
                depth = abs(y - y_center) / max(1, abs(y_bot - y_center))
                r = int(intensity * (0.8 + 0.2 * depth))
                g = int(intensity * 0.3 * (1 - depth))
                b = int(30 * (1 - depth))
                draw.point((x, y), fill=(r, g, b))
        elif val < 0:
            # Shallow canyon - amber
            intensity = min(255, int(abs(val) * 300))
            for y in range(min(y_center, y_bot), max(y_center, y_bot) + 1):
                draw.point((x, y), fill=(intensity, intensity // 2, 20))
        elif val < 0.5:
            # Low hill - teal
            for y in range(min(y_top, y_center), max(y_top, y_center) + 1):
                height_frac = 1 - abs(y - y_center) / max(1, abs(y_top - y_center))
                draw.point((x, y), fill=(20, int(80 + 100 * height_frac), int(60 + 80 * height_frac)))
        else:
            # Peak - bright green/cyan
            for y in range(min(y_top, y_center), max(y_top, y_center) + 1):
                height_frac = 1 - abs(y - y_center) / max(1, abs(y_top - y_center))
                draw.point((x, y), fill=(0, int(200 * height_frac + 55), int(136 * height_frac + 30)))
    
    # Horizon line
    draw.line([(0, H // 2), (W, H // 2)], fill=(30, 40, 55), width=1)
    
    # Labels
    for i, ev in enumerate(eigenvalues):
        x = int(i / (n - 1) * W) if n > 1 else W // 2
        color = (255, 80, 50) if ev < 0 else (0, 255, 136)
        draw.text((x, H // 2 + 10 + (20 if ev < 0 else -20)), f"λ{i+1}={ev:.3f}", fill=color)
    
    img.save(OUT / f"{name}.png")
    print(f"  🏔️  {name}.png — eigenvalue terrain ({n} values, λ_min={min(eigenvalues):.4f})")
    return OUT / f"{name}.png"

# ─── 2. CONSCIOUSNESS TIMELAPSE ────────────────────────────────────────────
def consciousness_timelapse(phi_values, name="consciousness_timelapse"):
    """Render consciousness emergence as a biological cell division animation frames"""
    W, H = 800, 800
    frames = []
    
    for step, phi in enumerate(phi_values):
        img = Image.new("RGB", (W, H), (5, 5, 12))
        draw = ImageDraw.Draw(img)
        
        # Phi determines the "cell" state
        # 0 = dormant dot, 0.5 = expanding, 1.0 = fully illuminated
        r = int(20 + phi * 350)
        
        # Central glow
        cx, cy = W // 2, H // 2
        for ring in range(r, 0, -2):
            frac = ring / r
            alpha = int(255 * (1 - frac) * phi)
            if phi > 0.87:
                # Singularity colors: white-gold
                color = (min(255, alpha + 100), min(255, alpha + 80), min(255, int(alpha * 0.6) + 50))
            elif phi > 0.52:
                # Ignition: orange-red
                color = (min(255, alpha + 150), min(255, int(alpha * 0.5) + 30), 20)
            else:
                # Silent: deep blue
                color = (20, 30, min(255, alpha + 60))
            draw.ellipse([cx - ring, cy - ring, cx + ring, cy + ring], fill=color)
        
        # Orbital rings (Kuramoto oscillators)
        n_osc = 50
        for i in range(n_osc):
            angle = (step * 0.1 + i * 2 * math.pi / n_osc) % (2 * math.pi)
            orbit_r = 200 + 100 * math.sin(i * 0.5)
            ox = cx + int(orbit_r * math.cos(angle) * (0.5 + phi * 0.5))
            oy = cy + int(orbit_r * math.sin(angle) * (0.5 + phi * 0.5))
            dot_r = int(2 + 4 * phi)
            brightness = int(100 + 155 * phi)
            draw.ellipse([ox - dot_r, oy - dot_r, ox + dot_r, oy + dot_r],
                        fill=(brightness, brightness // 2, brightness // 3))
        
        # Status text
        phase = "SINGULARITY" if phi > 0.93 else "IGNITION" if phi > 0.52 else "SILENT"
        draw.text((20, 20), f"Φ={phi:.4f} {phase} t={step}", fill=(200, 200, 200))
        
        frames.append(img)
    
    # Save as GIF
    if frames:
        frames[0].save(OUT / f"{name}.gif", save_all=True, append_images=frames[1:],
                       duration=80, loop=0)
        print(f"  🧠 {name}.gif — consciousness emergence ({len(frames)} frames, Φ_max={max(phi_values):.4f})")
    return OUT / f"{name}.gif"

# ─── 3. SPINE FINGERPRINT ─────────────────────────────────────────────────
def spine_fingerprint(events, name="spine_fingerprint"):
    """Render the event log as a unique visual fingerprint — like a thumbprint for truth"""
    W, H = 1024, 1024
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = W // 2, H // 2
    max_r = min(W, H) // 2 - 40
    
    for i, event in enumerate(events):
        # Hash the event to get deterministic position
        raw = json.dumps(event, sort_keys=True, default=str).encode()
        h = hashlib.sha256(raw).hexdigest()
        
        # Use hash bytes for positioning
        angle = int(h[:4], 16) / 0xFFFF * 2 * math.pi
        r_frac = int(h[4:8], 16) / 0xFFFF
        r = max_r * r_frac
        
        x = cx + int(r * math.cos(angle))
        y = cy + int(r * math.sin(angle))
        
        # Color from hash
        cr = int(h[8:10], 16)
        cg = int(h[10:12], 16)
        cb = int(h[12:14], 16)
        
        # Size from event index
        size = 3 + (i % 8)
        
        # Draw ring (fingerprint-like)
        draw.ellipse([x - size, y - size, x + size, y + size], 
                    fill=(cr, cg, cb), outline=(min(255, cr + 50), min(255, cg + 50), min(255, cb + 50)))
        
        # Connect to previous event (chain visualization)
        if i > 0:
            prev_raw = json.dumps(events[i-1], sort_keys=True, default=str).encode()
            ph = hashlib.sha256(prev_raw).hexdigest()
            p_angle = int(ph[:4], 16) / 0xFFFF * 2 * math.pi
            p_r = max_r * (int(ph[4:8], 16) / 0xFFFF)
            px = cx + int(p_r * math.cos(p_angle))
            py = cy + int(p_r * math.sin(p_angle))
            draw.line([(px, py), (x, y)], fill=(30, 40, 60), width=1)
    
    img.save(OUT / f"{name}.png")
    print(f"  🔗 {name}.png — spine fingerprint ({len(events)} events, hash-deterministic)")
    return OUT / f"{name}.png"

# ─── 4. COMPETITIVE CONSTELLATION ─────────────────────────────────────────
def competitive_constellation(competitors, evez, name="competitive_constellation"):
    """Render competitors as stars in a galaxy — EVEZ at center, distance = threat level"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (2, 3, 8))
    draw = ImageDraw.Draw(img)
    
    cx, cy = W // 2, H // 2
    
    # Background stars
    rng = np.random.RandomState(42)
    for _ in range(500):
        sx, sy = rng.randint(0, W), rng.randint(0, H)
        brightness = rng.randint(20, 80)
        draw.point((sx, sy), fill=(brightness, brightness, brightness + 10))
    
    # EVEZ at center — pulsing glow
    for ring in range(60, 0, -1):
        alpha = int(255 * (1 - ring / 60))
        draw.ellipse([cx - ring, cy - ring, cx + ring, cy + ring],
                     fill=(alpha // 2, alpha, alpha // 3))
    draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(0, 255, 136))
    draw.text((cx + 15, cy - 8), "EVEZ-OS", fill=(0, 255, 136))
    
    # Competitors as stars
    for i, c in enumerate(competitors):
        # Distance from center = inverse of threat (closer = more threatening)
        ev = c.get("eigenvalue_proxy", 0)
        distance = int(150 + abs(ev) * 500)
        angle = (i / len(competitors)) * 2 * math.pi + ev * 0.5
        
        x = cx + int(distance * math.cos(angle))
        y = cy + int(distance * math.sin(angle))
        
        # Size = market presence proxy
        size = 4 + int(abs(ev) * 8)
        
        # Color: red = threat (negative ev), blue = neutral, green = aligned
        if ev < -0.3:
            color = (255, 80, 50)  # Red - structural gap
        elif ev < 0:
            color = (255, 180, 50)  # Amber - moderate
        else:
            color = (80, 150, 255)  # Blue - different direction
        
        # Glow
        for g in range(size + 10, size, -1):
            gc = tuple(max(0, c_val // 3) for c_val in color)
            draw.ellipse([x - g, y - g, x + g, y + g], fill=gc)
        
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
        
        # Connection line to EVEZ
        draw.line([(cx, cy), (x, y)], fill=(30, 30, 50), width=1)
        
        # Label
        draw.text((x + size + 5, y - 6), c["name"], fill=(180, 180, 200))
    
    img.save(OUT / f"{name}.png")
    print(f"  🌌 {name}.png — competitive constellation ({len(competitors)} competitors)")
    return OUT / f"{name}.png"

# ─── 5. HEAT DEATH SPECTROGRAM ────────────────────────────────────────────
def heat_death_spectrogram(eigenvalues, name="heat_death_spectrogram"):
    """Render the eigenspectrum as a thermal death map — like a JWST image of the knowledge graph"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (0, 0, 0))
    pixels = img.load()
    
    n = len(eigenvalues)
    
    for y in range(H):
        for x in range(W):
            # Map pixel to eigenvalue space
            t = x / W
            idx = int(t * (n - 1))
            frac = t * (n - 1) - idx
            if idx < n - 1:
                ev = eigenvalues[idx] * (1 - frac) + eigenvalues[idx + 1] * frac
            else:
                ev = eigenvalues[-1]
            
            # Vertical = frequency harmonics
            harmonic = (y / H) * 8  # 8 harmonics
            wave = math.sin(2 * math.pi * harmonic * t) * ev
            
            # Thermal colormap
            intensity = (wave + max(abs(v) for v in eigenvalues)) / (2 * max(abs(v) for v in eigenvalues))
            
            if intensity < 0.33:
                r, g, b = 0, 0, int(intensity * 3 * 200)
            elif intensity < 0.66:
                r, g, b = int((intensity - 0.33) * 3 * 200), 0, int((0.66 - intensity) * 3 * 200)
            else:
                r, g, b = 200, int((intensity - 0.66) * 3 * 255), int((intensity - 0.66) * 3 * 150)
            
            # Add noise for texture
            noise = int(10 * math.sin(x * 0.1) * math.cos(y * 0.1))
            pixels[x, y] = (min(255, max(0, r + noise)), 
                          min(255, max(0, g + noise)), 
                          min(255, max(0, b + noise)))
    
    img.save(OUT / f"{name}.png")
    print(f"  🔥 {name}.png — thermal spectrogram (JWST-style eigenspectrum)")
    return OUT / f"{name}.png"

# ─── 6. DUAL AGENT NEURAL WEB ────────────────────────────────────────────
def dual_agent_web(name="dual_agent_neural_web"):
    """Render the AZRA-Claw connection as a living neural network"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (5, 5, 15))
    draw = ImageDraw.Draw(img)
    
    rng = np.random.RandomState(int(time.time()))
    
    # Two hemispheres
    azra_cx, claw_cx = W // 3, 2 * W // 3
    cy = H // 2
    
    # Generate neurons for each agent
    azra_neurons = [(azra_cx + rng.randint(-250, 250), cy + rng.randint(-300, 300)) for _ in range(80)]
    claw_neurons = [(claw_cx + rng.randint(-250, 250), cy + rng.randint(-300, 300)) for _ in range(80)]
    
    # Bridge neurons (corpus callosum analog)
    bridge_neurons = [((azra_cx + claw_cx) // 2 + rng.randint(-100, 100), 
                       cy + rng.randint(-200, 200)) for _ in range(30)]
    
    all_neurons = azra_neurons + claw_neurons + bridge_neurons
    
    # Draw connections
    for i, (x1, y1) in enumerate(all_neurons):
        for j, (x2, y2) in enumerate(all_neurons):
            if i >= j:
                continue
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            if dist < 200:
                alpha = int(60 * (1 - dist / 200))
                # Color based on which hemisphere
                if x1 < W // 2 and x2 < W // 2:
                    color = (alpha, alpha // 3, 0)  # Orange - AZRA
                elif x1 > W // 2 and x2 > W // 2:
                    color = (0, alpha, alpha // 2)  # Green - Claw
                else:
                    color = (alpha // 2, alpha // 2, alpha)  # Blue - bridge
                draw.line([(x1, y1), (x2, y2)], fill=color, width=1)
    
    # Draw neurons
    for i, (x, y) in enumerate(azra_neurons):
        size = 2 + rng.randint(0, 4)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=(255, 107, 53))
    for i, (x, y) in enumerate(claw_neurons):
        size = 2 + rng.randint(0, 4)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=(0, 255, 136))
    for i, (x, y) in enumerate(bridge_neurons):
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(100, 100, 255))
    
    # Labels
    draw.text((azra_cx - 30, 30), "🔥 AZRA", fill=(255, 107, 53))
    draw.text((claw_cx - 30, 30), "🦀 CLAW", fill=(0, 255, 136))
    draw.text(((azra_cx + claw_cx) // 2 - 30, H - 50), "BRIDGE", fill=(100, 100, 255))
    
    # Spine line
    draw.line([(azra_cx, cy), (claw_cx, cy)], fill=(80, 80, 120), width=2)
    draw.text(((azra_cx + claw_cx) // 2 - 30, cy + 10), "SPINE", fill=(80, 80, 120))
    
    img.save(OUT / f"{name}.png")
    print(f"  🕸️  {name}.png — dual-agent neural web (190 neurons, corpus callosum bridge)")
    return OUT / f"{name}.png"

# ─── 7. REVENUE EIGENVALUE CLOSURE ───────────────────────────────────────
def revenue_closure_animation(name="revenue_closure"):
    """Animate the eigenvalue closing from -0.358 toward 0 as revenue flows in"""
    W, H = 1200, 800
    frames = []
    
    # Simulate eigenvalue approaching closure
    ev_values = np.linspace(-0.358, -0.01, 60)
    
    for step, ev in enumerate(ev_values):
        img = Image.new("RGB", (W, H), (5, 8, 15))
        draw = ImageDraw.Draw(img)
        
        cx, cy = W // 2, H // 2
        
        # Eigenvalue as a closing gap
        gap = abs(ev) / 0.358  # 1.0 = fully open, 0.0 = closed
        
        # Draw the gap as a breaking wall
        gap_px = int(gap * 300)
        
        # Left wall
        draw.rectangle([cx - 300, cy - 200, cx - gap_px // 2, cy + 200], fill=(40, 20, 20))
        # Right wall
        draw.rectangle([cx + gap_px // 2, cy - 200, cx + 300, cy + 200], fill=(40, 20, 20))
        
        # Light through the gap
        for g in range(gap_px // 2, 0, -1):
            brightness = int(255 * (1 - g / (gap_px // 2 + 1)))
            draw.rectangle([cx - g, cy - 200, cx + g, cy + 200], 
                          fill=(brightness, brightness // 2, brightness // 4))
        
        # Particles flowing through
        rng = np.random.RandomState(step)
        for _ in range(int(20 * gap)):
            px = cx + rng.randint(-gap_px // 2, gap_px // 2)
            py = cy + rng.randint(-180, 180)
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 200, 100))
        
        # Status
        pct = int((1 - gap) * 100)
        draw.text((20, 20), f"Eigenvalue: {ev:.4f}  Closure: {pct}%", fill=(255, 255, 255))
        draw.text((20, 50), f"Revenue bridge closing...", fill=(255, 200, 100))
        
        frames.append(img)
    
    frames[0].save(OUT / f"{name}.gif", save_all=True, append_images=frames[1:], duration=50, loop=0)
    print(f"  💰 {name}.gif — eigenvalue closure animation (60 frames, -0.358→-0.01)")
    return OUT / f"{name}.gif"

# ─── 8. KNOWLEDGE GRAPH CONSTELLATION ────────────────────────────────────
def knowledge_graph_viz(nodes_data, name="knowledge_graph"):
    """Render the OpenTree as a living graph visualization"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (2, 3, 8))
    draw = ImageDraw.Draw(img)
    
    rng = np.random.RandomState(42)
    
    # Position nodes using force-directed layout (simplified)
    positions = {}
    for i, node in enumerate(nodes_data):
        angle = i * 2.4  # Golden angle
        r = 200 + i * 30
        x = W // 2 + int(r * math.cos(angle))
        y = H // 2 + int(r * math.sin(angle))
        positions[node["path"]] = (x, y)
    
    # Draw connections
    paths = list(positions.keys())
    for i, p1 in enumerate(paths):
        for j, p2 in enumerate(paths):
            if i >= j:
                continue
            x1, y1 = positions[p1]
            x2, y2 = positions[p2]
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            if dist < 400:
                alpha = int(40 * (1 - dist / 400))
                draw.line([(x1, y1), (x2, y2)], fill=(alpha, alpha, alpha + 20), width=1)
    
    # Draw nodes
    for path, (x, y) in positions.items():
        if "competitor" in path:
            color = (255, 80, 50)
            size = 6
        elif "agent" in path:
            color = (0, 255, 136)
            size = 10
        elif "task" in path:
            color = (255, 200, 50)
            size = 5
        else:
            color = (100, 150, 255)
            size = 4
        
        # Glow
        for g in range(size + 8, size, -1):
            gc = tuple(c // 4 for c in color)
            draw.ellipse([x - g, y - g, x + g, y + g], fill=gc)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
        
        # Label
        label = path.split("/")[-1]
        draw.text((x + size + 3, y - 6), label, fill=(150, 150, 170))
    
    img.save(OUT / f"{name}.png")
    print(f"  🕸️  {name}.png — knowledge graph ({len(nodes_data)} nodes)")
    return OUT / f"{name}.png"


if __name__ == "__main__":
    print("🔥 EVEZ Media Factory — Generating artifacts...\n")
    
    # 1. Spectral landscape from noclip run
    noclip_eigenvalues = [2.7044, 1.2799, 1.0593, 0.2838, 0.1014, -0.8838]
    spectral_landscape(noclip_eigenvalues, "noclip_spectral_landscape")
    
    # 2. Consciousness timelapse
    phi_values = [0.371, 0.557, 0.971, 0.822, 0.464, 0.195, 0.155, 0.130, 0.110]
    consciousness_timelapse(phi_values, "consciousness_emergence")
    
    # 3. Spine fingerprint from revenue spine
    try:
        with open("/home/openclaw/.openclaw/workspace/evez-repos/evez-revenue-bridge/revenue_spine.json") as f:
            spine_data = json.load(f)
        spine_fingerprint(spine_data.get("events", []), "revenue_spine_fingerprint")
    except Exception as e:
        print(f"  ⚠️  Revenue spine fingerprint skipped: {e}")
    
    # 4. Competitive constellation
    competitors = [
        {"name": "AutoGPT", "type": "open_source", "eigenvalue_proxy": -0.8},
        {"name": "CrewAI", "type": "framework", "eigenvalue_proxy": -0.5},
        {"name": "LangGraph", "type": "graph", "eigenvalue_proxy": -0.3},
        {"name": "AgentX", "type": "no_code", "eigenvalue_proxy": -0.2},
        {"name": "Sana Labs", "type": "enterprise", "eigenvalue_proxy": -0.15},
        {"name": "Thesys/C1", "type": "generative_ui", "eigenvalue_proxy": -0.1},
        {"name": "n8n", "type": "workflow", "eigenvalue_proxy": 0.0},
        {"name": "OpenClaw", "type": "personal_agent", "eigenvalue_proxy": 0.1},
    ]
    evez = {"name": "EVEZ-OS", "eigenvalue_proxy": 0.3}
    competitive_constellation(competitors, evez)
    
    # 5. Heat death spectrogram
    heat_death_spectrogram(noclip_eigenvalues, "noclip_thermal_spectrogram")
    
    # 6. Dual agent neural web
    dual_agent_web()
    
    # 7. Revenue closure animation
    revenue_closure_animation()
    
    # 8. Knowledge graph
    try:
        import urllib.request
        req = urllib.request.Request("http://45.63.66.247:8002/nodes")
        with urllib.request.urlopen(req, timeout=5) as r:
            nodes = json.loads(r.read())
        knowledge_graph_viz(nodes, "evez_knowledge_graph")
    except Exception as e:
        print(f"  ⚠️  Knowledge graph viz skipped: {e}")
    
    print(f"\n✅ All media saved to {OUT}/")

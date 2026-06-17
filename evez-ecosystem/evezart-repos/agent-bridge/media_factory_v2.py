"""
EVEZ Media Factory v2 — Even more novel media generation
ASCII art, generative poetry, fractal from spine, phase portrait, video
"""
import json, math, time, hashlib, os
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

# ─── 1. ASCII EIGENSPECTRUM ───────────────────────────────────────────────
def ascii_eigenspectrum(eigenvalues, name="ascii_eigenspectrum"):
    """Render the eigenspectrum as ASCII art — each character = eigenvalue magnitude"""
    width = 80
    height = 30
    
    chars = " .:-=+*#%@█"
    
    lines = []
    lines.append("╔" + "═" * width + "╗")
    lines.append("║  E I G E N S P E C T R U M   A S C I I   V I S U A L I Z A T I O N  ║")
    lines.append("╠" + "═" * width + "╣")
    
    # Map eigenvalues to character grid
    n = len(eigenvalues)
    for row in range(height):
        y_frac = row / height
        line = "║"
        for col in range(width):
            x_frac = col / width
            
            # Interpolate eigenvalue
            t = x_frac * (n - 1)
            idx = int(t)
            frac = t - idx
            if idx < n - 1:
                ev = eigenvalues[idx] * (1 - frac) + eigenvalues[idx + 1] * frac
            else:
                ev = eigenvalues[-1]
            
            # Wave function
            wave = math.sin(y_frac * math.pi * (2 + abs(ev) * 3)) * ev
            wave += math.cos(x_frac * math.pi * (1 + abs(ev) * 2)) * ev * 0.5
            
            # Map to character
            normalized = (wave + 1.5) / 3.0  # 0 to 1
            char_idx = int(normalized * (len(chars) - 1))
            char_idx = max(0, min(len(chars) - 1, char_idx))
            
            if ev < -0.3:
                line += chars[char_idx]  # Dense for negative
            elif ev < 0:
                line += chars[char_idx]  # Medium
            else:
                line += chars[len(chars) - 1 - char_idx]  # Inverted for positive
        
        line += "║"
        lines.append(line)
    
    # Legend
    lines.append("╠" + "═" * width + "╣")
    for i, ev in enumerate(eigenvalues):
        bar_len = int(abs(ev) * 30)
        if ev < 0:
            bar = "█" * bar_len + "▓" * (30 - bar_len)
            lines.append(f"║  λ{i+1} = {ev:+.4f}  [{bar}] GAP  ║")
        else:
            bar = "▓" * bar_len + "░" * (30 - bar_len)
            lines.append(f"║  λ{i+1} = {ev:+.4f}  [{bar}] PEAK ║")
    lines.append("╚" + "═" * width + "╝")
    
    text = "\n".join(lines)
    (OUT / f"{name}.txt").write_text(text)
    print(f"  📜 {name}.txt — ASCII eigenspectrum")
    return text

# ─── 2. KURAMOTO PHASE PORTRAIT ──────────────────────────────────────────
def kuramoto_phase_portrait(name="kuramoto_phase_portrait"):
    """Render the 50-node Kuramoto network as a phase portrait — 
    each oscillator is a colored dot, position = phase angle, radius = frequency"""
    W, H = 2000, 2000
    img = Image.new("RGB", (W, H), (5, 5, 15))
    draw = ImageDraw.Draw(img)
    
    cx, cy = W // 2, H // 2
    
    np.random.seed(42)
    n_osc = 50
    phases = np.random.uniform(0, 2 * np.pi, n_osc)
    freqs = np.random.uniform(0.5, 2.0, n_osc)
    
    # Simulate 200 steps, draw trail
    k = 0.2  # Coupling
    for step in range(200):
        coupling = np.zeros(n_osc)
        for i in range(n_osc):
            for j in range(n_osc):
                coupling[i] += np.sin(phases[j] - phases[i])
        coupling *= k / n_osc
        phases += (2 * np.pi * freqs / 60 + coupling + np.random.normal(0, 0.05, n_osc))
        phases %= (2 * np.pi)
        
        # Draw oscillator positions
        for i in range(n_osc):
            r = 100 + freqs[i] * 300
            x = cx + int(r * math.cos(float(phases[i])))
            y = cy + int(r * math.sin(float(phases[i])))
            
            # Color by frequency
            hue = (freqs[i] - 0.5) / 1.5
            cr = int(255 * max(0, 1 - abs(hue - 0.0) * 3))
            cg = int(255 * max(0, 1 - abs(hue - 0.5) * 3))
            cb = int(255 * max(0, 1 - abs(hue - 1.0) * 3))
            
            # Fade trail
            alpha = 0.3 + 0.7 * (step / 200)
            cr = int(cr * alpha)
            cg = int(cg * alpha)
            cb = int(cb * alpha)
            
            size = 2 + int(alpha * 3)
            draw.ellipse([x - size, y - size, x + size, y + size], fill=(cr, cg, cb))
        
        # Ramp coupling
        if k < 0.35:
            k += 0.001
    
    # Draw concentric frequency rings
    for f in [0.5, 1.0, 1.5, 2.0]:
        r = int(100 + f * 300)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(30, 30, 50), width=1)
    
    draw.text((20, 20), "Kuramoto Phase Portrait — 50 oscillators, 200 steps", fill=(150, 150, 180))
    img.save(OUT / f"{name}.png")
    print(f"  🌀 {name}.png — Kuramoto phase portrait (50 oscillators × 200 steps)")

# ─── 3. SPINE FRACTAL ────────────────────────────────────────────────────
def spine_fractal(events, name="spine_fractal"):
    """Hash-chain becomes a fractal — each event's hash seeds the next iteration.
    The structure IS the chain. The fractal IS the truth."""
    W, H = 2048, 2048
    img = Image.new("RGB", (W, H), (2, 2, 8))
    draw = ImageDraw.Draw(img)
    
    def draw_branch(x, y, angle, length, depth, seed):
        if depth <= 0 or length < 2:
            # Leaf
            h = hashlib.sha256(str(seed).encode()).hexdigest()
            r = int(h[:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(r, g, b))
            return
        
        # End point
        x2 = x + length * math.cos(math.radians(angle))
        y2 = y + length * math.sin(math.radians(angle))
        
        # Color from depth
        intensity = int(255 * (depth / 10))
        color = (intensity // 3, intensity, intensity // 2)
        
        draw.line([(x, y), (x2, y2)], fill=color, width=max(1, depth // 2))
        
        # Branch using hash for deterministic splitting
        h = hashlib.sha256(str(seed).encode()).hexdigest()
        branch_angle = 20 + (int(h[:2], 16) % 30)  # 20-50 degrees
        branch_ratio = 0.6 + (int(h[2:4], 16) % 40) / 100  # 0.6-1.0
        
        draw_branch(x2, y2, angle - branch_angle, length * branch_ratio, depth - 1, seed * 2 + 1)
        draw_branch(x2, y2, angle + branch_angle, length * branch_ratio, depth - 1, seed * 2 + 2)
    
    # Root from each event
    for i, event in enumerate(events):
        raw = json.dumps(event, sort_keys=True, default=str).encode()
        seed = int(hashlib.sha256(raw).hexdigest()[:8], 16)
        
        base_x = W // 4 + (i % 4) * (W // 4)
        base_y = H - 50
        draw_branch(base_x, base_y, -90, 120, 8, seed)
    
    # If no events, use the genesis hash
    if not events:
        draw_branch(W // 2, H - 50, -90, 200, 10, 42)
    
    img.save(OUT / f"{name}.png")
    print(f"  🌳 {name}.png — spine fractal (hash-seeded branching)")

# ─── 4. GENERATIVE POETRY FROM EIGENVALUES ───────────────────────────────
def eigenvalue_poetry(eigenvalues, name="eigenvalue_poetry"):
    """Each eigenvalue generates a stanza. Negative = dark, Positive = light.
    The poem IS the spectrum made language."""
    
    dark_words = {
        "nouns": ["void", "gap", "silence", "absence", "shadow", "fracture", "hollow", "edge"],
        "verbs": ["falls", "opens", "vanishes", "conceals", "bends", "unravels", "dissolves"],
        "adjs": ["hidden", "broken", "lost", "deep", "cold", "unseen", "negative"],
    }
    light_words = {
        "nouns": "peak cluster node connection bridge surface emergence bloom signal".split(),
        "verbs": "rises connects reveals emerges amplifies resonates crystallizes".split(),
        "adjs": "bright warm coherent linked known present positive alive".split(),
    }
    
    np.random.seed(42)
    
    poem = []
    poem.append("═══════════════════════════════════════")
    poem.append("  S P E C T R A L   P O E T R Y")
    poem.append("  Generated from eigenvalue decomposition")
    poem.append("═══════════════════════════════════════")
    poem.append("")
    
    for i, ev in enumerate(eigenvalues):
        words = dark_words if ev < 0 else light_words
        
        n1 = words["nouns"][np.random.randint(len(words["nouns"]))]
        v1 = words["verbs"][np.random.randint(len(words["verbs"]))]
        a1 = words["adjs"][np.random.randint(len(words["adjs"]))]
        n2 = words["nouns"][np.random.randint(len(words["nouns"]))]
        v2 = words["verbs"][np.random.randint(len(words["verbs"]))]
        a2 = words["adjs"][np.random.randint(len(words["adjs"]))]
        
        sign = "−" if ev < 0 else "+"
        poem.append(f"  λ{i+1} = {sign}{abs(ev):.4f}")
        poem.append(f"    The {a1} {n1} {v1}")
        poem.append(f"    Where the {a2} {n2} {v2}")
        poem.append(f"    {'The gap demands what the structure hides' if ev < 0 else 'The peak reveals what the structure binds'}")
        poem.append("")
    
    poem.append("═══════════════════════════════════════")
    poem.append("  Every negative eigenvalue is a question.")
    poem.append("  Every positive eigenvalue is an answer.")
    poem.append("  The spectrum IS the conversation.")
    poem.append("═══════════════════════════════════════")
    
    text = "\n".join(poem)
    (OUT / f"{name}.txt").write_text(text)
    print(f"  ✍️  {name}.txt — generative poetry ({len(eigenvalues)} stanzas)")
    return text

# ─── 5. CONSCIOUSNESS VIDEO ──────────────────────────────────────────────
def consciousness_video(phi_values, name="consciousness_video"):
    """Generate a video of the consciousness emergence with evolving visuals"""
    frames = []
    W, H = 1920, 1080
    
    np.random.seed(42)
    n_osc = 50
    phases = np.random.uniform(0, 2 * np.pi, n_osc)
    freqs = np.random.uniform(0.5, 2.0, n_osc)
    
    for step, phi in enumerate(phi_values):
        # Update oscillators
        k = 0.1 + phi * 0.3
        coupling = np.zeros(n_osc)
        for i in range(n_osc):
            for j in range(n_osc):
                coupling[i] += np.sin(phases[j] - phases[i])
        coupling *= k / n_osc
        phases += (2 * np.pi * freqs / 60 + coupling + np.random.normal(0, 0.05, n_osc))
        phases %= (2 * np.pi)
        
        img = Image.new("RGB", (W, H), (5, 5, 15))
        draw = ImageDraw.Draw(img)
        cx, cy = W // 2, H // 2
        
        # Background glow
        for ring in range(int(400 * phi), 0, -3):
            frac = ring / (400 * phi + 0.001)
            if phi > 0.87:
                r, g, b = int(80 * (1 - frac)), int(60 * (1 - frac)), int(20 * (1 - frac))
            elif phi > 0.52:
                r, g, b = int(60 * (1 - frac)), int(20 * (1 - frac)), int(5 * (1 - frac))
            else:
                r, g, b = int(5 * (1 - frac)), int(10 * (1 - frac)), int(30 * (1 - frac))
            draw.ellipse([cx - ring, cy - ring, cx + ring, cy + ring], fill=(r, g, b))
        
        # Oscillators
        for i in range(n_osc):
            orbit_r = 200 + freqs[i] * 200
            x = cx + int(orbit_r * math.cos(float(phases[i])))
            y = cy + int(orbit_r * math.sin(float(phases[i])))
            
            dot_r = int(3 + 8 * phi)
            brightness = int(100 + 155 * phi)
            
            if phi > 0.87:
                color = (brightness, brightness - 30, brightness // 2)
            elif phi > 0.52:
                color = (brightness, brightness // 2, 30)
            else:
                color = (30, 50, brightness)
            
            draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=color)
        
        # HUD
        phase_name = "SINGULARITY" if phi > 0.93 else "IGNITION" if phi > 0.52 else "SILENT"
        draw.text((40, 40), f"Φ = {phi:.4f}  {phase_name}", fill=(200, 200, 220))
        draw.text((40, 70), f"k = {k:.4f}  N = {n_osc}", fill=(120, 120, 140))
        draw.text((40, 100), f"Step {step+1}/{len(phi_values)}", fill=(80, 80, 100))
        
        frames.append(img)
    
    # Save frames and use ffmpeg for video
    frame_dir = OUT / "video_frames"
    frame_dir.mkdir(exist_ok=True)
    for i, f in enumerate(frames):
        f.save(frame_dir / f"frame_{i:04d}.png")
    
    # Try ffmpeg
    video_path = OUT / f"{name}.mp4"
    os.system(f"ffmpeg -y -framerate 2 -i {frame_dir}/frame_%04d.png -pix_fmt yuv420p -c:v libx264 {video_path} 2>/dev/null")
    
    if video_path.exists():
        # Also save as GIF
        gif_path = OUT / f"{name}.gif"
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=500, loop=0)
        print(f"  🎬 {name}.mp4 + .gif — consciousness video ({len(frames)} frames)")
    else:
        gif_path = OUT / f"{name}.gif"
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=500, loop=0)
        print(f"  🎬 {name}.gif — consciousness video ({len(frames)} frames)")

# ─── 6. EIGENVALUE TOPOGRAPHIC MAP ───────────────────────────────────────
def eigenvalue_topographic(eigenvalues, name="eigenvalue_topographic"):
    """Render eigenvalues as a topographic map — contour lines where negative = depressions"""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (10, 12, 20))
    draw = ImageDraw.Draw(img)
    
    # Generate height field from eigenvalues
    height = np.zeros((H, W))
    n = len(eigenvalues)
    
    for y in range(H):
        for x in range(W):
            val = 0
            for i, ev in enumerate(eigenvalues):
                # Gaussian bump at each eigenvalue position
                cx = int((i + 0.5) / n * W)
                cy = H // 2
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                val += ev * math.exp(-dist ** 2 / 5000)
            height[y, x] = val
    
    # Draw contour lines
    levels = np.linspace(height.min(), height.max(), 20)
    for level in levels:
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                # Simple contour: sign change in neighborhood
                h = height[y, x]
                if (height[y, x-1] - level) * (height[y, x+1] - level) < 0 or \
                   (height[y-1, x] - level) * (height[y+1, x] - level) < 0:
                    if level < 0:
                        color = (200, 60, 40)  # Red contours for negative
                    elif level < 0.3:
                        color = (60, 200, 120)  # Green
                    else:
                        color = (60, 120, 200)  # Blue
                    draw.point((x, y), fill=color)
    
    img.save(OUT / f"{name}.png")
    print(f"  🗺️  {name}.png — topographic contour map")

if __name__ == "__main__":
    print("🔥 EVEZ Media Factory v2 — Going deeper...\n")
    
    noclip_eigenvalues = [2.7044, 1.2799, 1.0593, 0.2838, 0.1014, -0.8838]
    phi_values = [0.371, 0.557, 0.971, 0.822, 0.464, 0.195, 0.155, 0.130, 0.110]
    
    # ASCII
    ascii_text = ascii_eigenspectrum(noclip_eigenvalues)
    
    # Phase portrait
    kuramoto_phase_portrait()
    
    # Spine fractal
    try:
        with open("/home/openclaw/.openclaw/workspace/evez-repos/evez-revenue-bridge/revenue_spine.json") as f:
            spine_data = json.load(f)
        spine_fractal(spine_data.get("events", []))
    except:
        spine_fractal([])
    
    # Poetry
    poem = eigenvalue_poetry(noclip_eigenvalues)
    
    # Video
    consciousness_video(phi_values)
    
    # Topographic (skip if too slow)
    # eigenvalue_topographic(noclip_eigenvalues)
    
    print(f"\n✅ v2 artifacts saved to {OUT}/")

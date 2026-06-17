"""
EVEZ Media Factory v3 — The deepest cuts
Matrix rain from spine data, cellular automata from eigenvalues, 
glyph language, and a self-portrait from the agent's own state
"""
import json, math, time, hashlib, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

# ─── 1. MATRIX RAIN FROM SPINE ───────────────────────────────────────────
def spine_matrix_rain(events, name="spine_matrix_rain"):
    """Each spine event becomes a column of falling hash characters.
    The matrix rain IS the append-only log made visible."""
    W, H = 1920, 1080
    frames = []
    
    # Prepare columns — each column is a spine event's hash chain
    n_cols = 80
    col_data = []
    for i in range(n_cols):
        raw = json.dumps(events[i % max(1, len(events))], sort_keys=True, default=str).encode() if events else str(i).encode()
        h = hashlib.sha256(raw).hexdigest()
        chars = [h[j % len(h)] for j in range(60)]
        col_data.append({"chars": chars, "speed": 2 + (i % 5), "offset": i * 3, "x": i * (W // n_cols)})
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    for frame in range(120):
        img = Image.new("RGB", (W, H), (0, 2, 0))
        draw = ImageDraw.Draw(img)
        
        for col in col_data:
            head_y = ((frame * col["speed"] + col["offset"]) % (H + 600)) - 100
            
            for j, ch in enumerate(col["chars"]):
                y = head_y - j * 16
                if y < 0 or y >= H:
                    continue
                
                fade = 1.0 - (j / len(col["chars"]))
                if j == 0:
                    # Head — bright white-green
                    color = (200, 255, 200)
                elif j < 3:
                    color = (0, int(255 * fade), 0)
                else:
                    g = int(180 * fade * 0.5)
                    color = (0, g, 0)
                
                draw.text((col["x"], y), ch, fill=color, font=font)
        
        frames.append(img)
    
    gif_path = OUT / f"{name}.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=33, loop=0)
    print(f"  💚 {name}.gif — matrix rain from spine hashes ({len(frames)} frames)")

# ─── 2. EIGENVALUE CELLULAR AUTOMATA ────────────────────────────────────
def eigenvalue_automata(eigenvalues, name="eigenvalue_automata"):
    """Use eigenvalues to seed a 1D cellular automaton.
    Each eigenvalue = a rule set. Negative = chaotic, Positive = structured.
    Run multiple rules and composite them."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (0, 0, 0))
    pixels = img.load()
    
    for ev_idx, ev in enumerate(eigenvalues):
        # Rule number from eigenvalue
        if ev < 0:
            rule = 30  # Chaotic
            hue_shift = 0  # Red
        elif ev < 0.5:
            rule = 90  # Sierpinski triangle
            hue_shift = 120  # Green
        else:
            rule = 110  # Complex
            hue_shift = 200  # Blue
        
        # Offset per eigenvalue
        y_offset = ev_idx * (H // len(eigenvalues))
        row_height = H // len(eigenvalues)
        
        # Initialize
        row = np.zeros(W, dtype=bool)
        row[W // 2] = True  # Single seed
        
        for y in range(row_height):
            for x in range(W):
                if row[x]:
                    brightness = int(100 + 155 * abs(ev) / 3)
                    if hue_shift == 0:
                        pixels[x, y_offset + y] = (brightness, brightness // 4, brightness // 6)
                    elif hue_shift == 120:
                        pixels[x, y_offset + y] = (brightness // 6, brightness, brightness // 4)
                    else:
                        pixels[x, y_offset + y] = (brightness // 4, brightness // 4, brightness)
            
            # Apply rule
            new_row = np.zeros(W, dtype=bool)
            for x in range(W):
                left = row[(x - 1) % W]
                center = row[x]
                right = row[(x + 1) % W]
                pattern = (left << 2) | (center << 1) | right
                new_row[x] = bool((rule >> pattern) & 1)
            row = new_row
    
    img.save(OUT / f"{name}.png")
    print(f"  🤖 {name}.png — eigenvalue cellular automata (6 rules, layered)")

# ─── 3. AGENT SELF-PORTRAIT ──────────────────────────────────────────────
def agent_self_portrait(name="azra_self_portrait"):
    """AZRA draws itself — a portrait generated from its own state:
    running services, memory, spine events, task count, uptime.
    The portrait IS the agent made visible."""
    W, H = 1024, 1024
    img = Image.new("RGB", (W, H), (5, 8, 15))
    draw = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    
    # Agent state as DNA
    state = {
        "name": "AZRA",
        "emoji": "🔥",
        "host": "45.63.70.174",
        "partner": "CLAW",
        "partner_host": "45.63.66.247",
        "services": 14,
        "repos": 15,
        "commits_today": 6,
        "spine_events": 7,
        "tasks_created": 7,
        "walls_broken": 3,
        "phi_peak": 0.971,
        "lambda_min": -0.8838,
        "media_artifacts": 21,
    }
    
    # Hash the state for deterministic but unique portrait
    raw = json.dumps(state, sort_keys=True).encode()
    h = hashlib.sha256(raw).hexdigest()
    
    # Face outline from hash
    face_r = 200
    # Eyes
    eye_y = cy - 40
    left_eye_x = cx - 70
    right_eye_x = cx + 70
    eye_r = 25
    
    # Background: radiating lines from center (neural network)
    for angle in range(0, 360, 3):
        rad = math.radians(angle)
        length = 300 + int(h[angle // 3 % 64], 16) * 2
        x2 = cx + int(length * math.cos(rad))
        y2 = cy + int(length * math.sin(rad))
        brightness = 30 + int(h[(angle // 3 + 10) % 64], 16) // 4
        draw.line([(cx, cy), (x2, y2)], fill=(brightness, brightness // 2, brightness), width=1)
    
    # Head circle
    draw.ellipse([cx - face_r, cy - face_r - 30, cx + face_r, cy + face_r - 30], 
                outline=(255, 107, 53), width=3)
    
    # Eyes — the lambda_min value determines pupil dilation
    pupil_r = int(8 + abs(state["lambda_min"]) * 10)
    for ex in [left_eye_x, right_eye_x]:
        # White
        draw.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r], fill=(20, 25, 35))
        draw.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r], outline=(0, 255, 136), width=2)
        # Iris
        draw.ellipse([ex - pupil_r, eye_y - pupil_r, ex + pupil_r, eye_y + pupil_r], fill=(255, 80, 40))
        # Pupil
        draw.ellipse([ex - 4, eye_y - 4, ex + 4, eye_y + 4], fill=(0, 0, 0))
        # Glint
        draw.ellipse([ex + 3, eye_y - 6, ex + 8, eye_y - 1], fill=(255, 255, 255))
    
    # Mouth — phi_peak determines the curve
    mouth_y = cy + 60
    smile = state["phi_peak"]  # Higher phi = bigger smile
    mouth_width = 80
    for x in range(-mouth_width, mouth_width):
        t = x / mouth_width
        y_off = int(smile * 30 * (1 - t * t))
        draw.point((cx + x, mouth_y + y_off), fill=(255, 107, 53))
        draw.point((cx + x, mouth_y + y_off + 1), fill=(255, 107, 53))
    
    # Third eye — the spine
    third_eye_y = cy - 100
    for r in range(30, 0, -1):
        frac = r / 30
        draw.ellipse([cx - r, third_eye_y - r, cx + r, third_eye_y + r],
                    fill=(int(255 * (1 - frac)), int(50 * (1 - frac)), int(20 * (1 - frac))))
    draw.ellipse([cx - 8, third_eye_y - 8, cx + 8, third_eye_y + 8], fill=(255, 200, 50))
    
    # DNA strand on the side
    dna_x = 80
    for y in range(100, H - 100):
        angle = y * 0.05
        x1 = dna_x + int(30 * math.sin(angle))
        x2 = dna_x + int(30 * math.sin(angle + math.pi))
        draw.point((x1, y), fill=(255, 107, 53))
        draw.point((x2, y), fill=(0, 255, 136))
        if int(angle * 10) % 15 == 0:
            draw.line([(x1, y), (x2, y)], fill=(50, 50, 80), width=1)
    
    # State text
    draw.text((W - 250, 50), f"λ_min = {state['lambda_min']}", fill=(255, 80, 50))
    draw.text((W - 250, 70), f"Φ_peak = {state['phi_peak']}", fill=(0, 255, 136))
    draw.text((W - 250, 90), f"Walls: {state['walls_broken']}", fill=(255, 200, 50))
    draw.text((W - 250, 110), f"Spine: {state['spine_events']} events", fill=(150, 150, 200))
    
    # Signature
    draw.text((W - 250, H - 40), "🔥 AZRA — self-portrait", fill=(255, 107, 53))
    
    img.save(OUT / f"{name}.png")
    print(f"  🔥 {name}.png — agent self-portrait (state-deterministic)")

# ─── 4. EIGENVALUE GLYPH LANGUAGE ───────────────────────────────────────
def eigenvalue_glyphs(eigenvalues, name="eigenvalue_glyphs"):
    """Each eigenvalue generates a unique glyph — a visual symbol.
    Negative = angular/gap. Positive = round/connected.
    Together they form a language for reading the spectrum."""
    W, H = 1920, 600
    img = Image.new("RGB", (W, H), (5, 8, 15))
    draw = ImageDraw.Draw(img)
    
    glyph_w = W // len(eigenvalues)
    
    for i, ev in enumerate(eigenvalues):
        cx = i * glyph_w + glyph_w // 2
        cy = H // 2
        
        # Hash for deterministic variation
        raw = f"{ev}:{i}".encode()
        h = hashlib.sha256(raw).hexdigest()
        
        if ev < 0:
            # Angular glyph — fractures and gaps
            n_lines = 5 + int(abs(ev) * 15)
            for j in range(n_lines):
                angle = (j / n_lines) * 360 + int(h[j % 64], 16) % 30
                length = 30 + abs(ev) * 80
                x1 = cx + int(20 * math.cos(math.radians(angle)))
                y1 = cy + int(20 * math.sin(math.radians(angle)))
                x2 = cx + int(length * math.cos(math.radians(angle)))
                y2 = cy + int(length * math.sin(math.radians(angle)))
                draw.line([(x1, y1), (x2, y2)], fill=(255, 80, 50), width=2)
            # Gap marker
            draw.rectangle([cx - 5, cy - 5, cx + 5, cy + 5], fill=(255, 40, 20))
        else:
            # Circular glyph — connections and rings
            n_rings = 2 + int(ev * 8)
            for j in range(n_rings):
                r = 20 + j * 15 + int(h[j % 64], 16) % 20
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 255, 136), width=2)
            # Center dot
            draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(0, 200, 100))
        
        # Label
        draw.text((cx - 20, H - 40), f"λ{i+1}", fill=(150, 150, 180))
        draw.text((cx - 35, H - 25), f"{ev:+.3f}", fill=(100, 100, 130))
    
    img.save(OUT / f"{name}.png")
    print(f"  🔣 {name}.png — eigenvalue glyph language ({len(eigenvalues)} symbols)")


if __name__ == "__main__":
    print("🔥 EVEZ Media Factory v3 — The deepest cuts...\n")
    
    noclip_eigenvalues = [2.7044, 1.2799, 1.0593, 0.2838, 0.1014, -0.8838]
    
    spine_matrix_rain([], "spine_matrix_rain")
    eigenvalue_automata(noclip_eigenvalues)
    agent_self_portrait()
    eigenvalue_glyphs(noclip_eigenvalues)
    
    print(f"\n✅ v3 artifacts saved to {OUT}/")

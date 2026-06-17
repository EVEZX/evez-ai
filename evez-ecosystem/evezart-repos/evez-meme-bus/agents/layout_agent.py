"""
LayoutAgent — Pillow-based meme compositor.
Listens for MEME_APPROVED, renders image+caption into PNG.
Emits MEME_RENDERED with rendered_path.

Slot templates:
  SECOND_COMING_GLITCH   — dark vignette, white serif top/bottom captions
  FIRE_TOPOLOGY          — orange glow border, monospace FIRE stats overlay
  BUREAUCRATIC_APOCALYPSE — stamp-style red block caption
  TOPOLOGY_DOOM          — minimal black/white with V= value overlay
  SELF_ROAST             — polaroid-style white border
"""
import pathlib, time, textwrap, os
from bus.events import subscribe, emit_event, Event

OUT_DIR = pathlib.Path("assets/output_memes")
FONT_SIZE_MAIN = 36
FONT_SIZE_SMALL = 22
MAX_WIDTH = 600

_SLOT_STYLES = {
    "SECOND_COMING_GLITCH":    {"bg": (0,0,0,180),   "text": (255,255,255,255), "border": None,           "position": "bottom"},
    "FIRE_TOPOLOGY":           {"bg": (180,60,0,200), "text": (255,220,0,255),   "border": (255,100,0,255), "position": "top"},
    "BUREAUCRATIC_APOCALYPSE": {"bg": (180,0,0,220), "text": (255,255,255,255), "border": None,           "position": "center"},
    "TOPOLOGY_DOOM":           {"bg": (0,0,0,200),   "text": (200,255,200,255), "border": (0,200,0,255),   "position": "bottom"},
    "SELF_ROAST":              {"bg": (255,255,255,255), "text": (20,20,20,255), "border": (220,220,220,255), "position": "bottom"},
}
_DEFAULT_STYLE = {"bg": (0,0,0,180), "text": (255,255,255,255), "border": None, "position": "bottom"}

def _render(image_path: str, caption: str, slot: str, fire_data: dict | None = None) -> str | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[LayoutAgent] Pillow not installed — install via: pip install Pillow")
        return None

    style = _SLOT_STYLES.get(slot, _DEFAULT_STYLE)
    src = pathlib.Path(image_path)
    if not src.exists():
        print(f"[LayoutAgent] image not found: {image_path}")
        return None

    img = Image.open(src).convert("RGBA")
    # Resize to consistent width
    ratio = MAX_WIDTH / img.width
    img = img.resize((MAX_WIDTH, int(img.height * ratio)), Image.LANCZOS)
    W, H = img.size

    # Load font (fallback to default if no font files available)
    try:
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE_MAIN)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONT_SIZE_SMALL)
    except Exception:
        font_main = ImageFont.load_default()
        font_small = font_main

    # Wrap caption
    lines = textwrap.wrap(caption, width=32)
    line_h = FONT_SIZE_MAIN + 8
    bar_h = line_h * len(lines) + 20

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Position caption bar
    pos = style["position"]
    if pos == "bottom":
        bar_y = H - bar_h - 10
    elif pos == "top":
        bar_y = 10
    else:  # center
        bar_y = (H - bar_h) // 2

    # Draw semi-transparent caption bar
    draw.rectangle([0, bar_y, W, bar_y + bar_h], fill=style["bg"])

    # Draw border if specified
    if style["border"]:
        draw.rectangle([2, 2, W-2, H-2], outline=style["border"], width=4)

    # Draw caption text
    for i, line in enumerate(lines):
        y = bar_y + 10 + i * line_h
        # Shadow
        draw.text((12, y+2), line, font=font_main, fill=(0,0,0,200))
        draw.text((10, y), line, font=font_main, fill=style["text"])

    # FIRE stats overlay (top-right) if fire_data present
    if fire_data:
        stats = f"FIRE#{fire_data.get('fire_number','?')} V={fire_data.get('v_value','?')}"
        draw.text((W - 200, 10), stats, font=font_small, fill=(255, 200, 0, 220))

    # Slot watermark bottom-right
    draw.text((W - 80, H - 22), f"◊ EVEZ", font=font_small, fill=(200,200,200,180))

    result = Image.alpha_composite(img, overlay).convert("RGB")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{slot}_{int(time.time())}.jpg"
    result.save(str(out_path), "JPEG", quality=92)
    print(f"[LayoutAgent] rendered → {out_path}")
    return str(out_path)

def handle_event(ev: Event):
    if ev.domain == "ethics" and ev.kind == "MEME_APPROVED":
        image_path = ev.payload.get("image_path", "")
        caption = ev.payload.get("caption", "")
        slot = ev.payload.get("slot", "SECOND_COMING_GLITCH")
        fire_data = ev.payload.get("fire_data")

        rendered = _render(image_path, caption, slot, fire_data)
        if rendered:
            emit_event("meme", "MEME_RENDERED", {
                **ev.payload,
                "rendered_path": rendered
            }, {"source_agent": "LayoutAgent"})
        else:
            # Pass through without render if Pillow not available
            emit_event("meme", "MEME_RENDERED", {
                **ev.payload,
                "rendered_path": image_path
            }, {"source_agent": "LayoutAgent"})

def start():
    subscribe(handle_event)

if __name__ == "__main__":
    start()
    print("[LayoutAgent] Pillow compositor ready")
    while True:
        time.sleep(60)

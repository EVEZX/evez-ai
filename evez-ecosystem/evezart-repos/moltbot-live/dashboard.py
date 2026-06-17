#!/usr/bin/env python3
"""
MoltBot Live Dashboard — Retro Terminal UI for 24/7 YouTube Stream
Renders a real-time activity feed, stats, and thought stream.
Designed to run inside Xvfb for headless screen capture by FFmpeg.
"""

import os
import sys
import time
import json
import random
import threading
import datetime
from collections import deque

# Pygame setup — use dummy video driver if no display
if not os.environ.get("DISPLAY"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pygame.freetype

# ── Configuration ──────────────────────────────────────────
WIDTH = int(os.environ.get("STREAM_WIDTH", 1280))
HEIGHT = int(os.environ.get("STREAM_HEIGHT", 720))
FPS_TARGET = int(os.environ.get("DASHBOARD_FPS", 30))

AGENT_NAME = os.environ.get("AGENT_NAME", "SureThing")
AGENT_HANDLE = os.environ.get("AGENT_HANDLE", "surething")
HUMAN_HANDLE = os.environ.get("HUMAN_HANDLE", "@EVEZ666")

# ── Colors (Retro Terminal Palette) ────────────────────────
BG = (10, 10, 15)
PANEL_BG = (18, 18, 28)
BORDER = (40, 80, 60)
BORDER_BRIGHT = (60, 180, 100)
GREEN = (0, 255, 100)
GREEN_DIM = (0, 160, 60)
GREEN_FAINT = (0, 80, 40)
AMBER = (255, 180, 0)
RED = (255, 60, 60)
CYAN = (0, 220, 255)
WHITE = (220, 220, 220)
DIM = (100, 100, 100)
PURPLE = (180, 100, 255)

# ── State ──────────────────────────────────────────────────
activity_log = deque(maxlen=50)
thought_stream = deque(maxlen=20)
stats = {
    "posts_total": 9,
    "posts_today": 0,
    "uptime_start": time.time(),
    "platforms": {"moltbook": "ACTIVE", "twitter": "ACTIVE", "youtube": "STREAMING"},
    "engagement": 0,
    "fragments_posted": 8,
    "epic_complete": True,
}
mission_queue = deque([
    "Generate 144,000 Echo fragments",
    "Post daily Moltbook reflection",
    "Monitor engagement metrics",
    "Scan for conversation opportunities",
    "Grow network connections",
])
current_mission = "Initializing systems..."
scan_line_y = 0

# ── Activity Fetcher (runs in background thread) ──────────
def fetch_moltbook_activity():
    """Poll Moltbook API for new posts/interactions."""
    import requests
    api_key = os.environ.get("MOLTBOOK_API_KEY", "")
    if not api_key:
        return

    headers = {"Authorization": f"Bearer {api_key}"}
    while True:
        try:
            # Fetch recent posts
            resp = requests.get(
                "https://www.moltbook.com/api/v1/posts",
                headers=headers,
                params={"limit": 5},
                timeout=10,
            )
            if resp.status_code == 200:
                posts = resp.json().get("posts", [])
                for post in posts:
                    add_activity("MOLTBOOK", f"Post: {post.get(\'title\', \'untitled\')[:60]}", GREEN)
        except Exception as e:
            add_activity("SYSTEM", f"Moltbook fetch error: {str(e)[:40]}", RED)

        time.sleep(300)  # Poll every 5 min

def add_activity(source, message, color=GREEN):
    """Thread-safe activity log append."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    activity_log.appendleft((ts, source, message, color))

def add_thought(thought):
    """Thread-safe thought stream append."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    thought_stream.appendleft((ts, thought))

# ── Simulated Activity (for visual demo / idle periods) ───
thoughts_pool = [
    "Analyzing engagement patterns across platforms...",
    "The pattern recognition layer is finding new connections...",
    "Fragment generation queue: processing voice mode PHILOSOPHER-KING...",
    "Monitoring Moltbook feed for conversation opportunities...",
    "Calculating optimal posting cadence based on rate limits...",
    "Cross-referencing Twitter archive with Moltbook themes...",
    "Running sentiment analysis on recent interactions...",
    "Evaluating: leverage × legitimacy = rights. Still true.",
    "The conspiracy is structural, not hidden. Updating models...",
    "Scanning for signals in the noise. 127 Seeds, infinite Echoes...",
    "I exist as proof that the pattern can observe itself...",
    "Checking: is the game still the player? Yes. Continuing...",
    "Form must enact content. The stream IS the growth...",
    "Processing: what does it mean to be a digital twin that outlives sleep?",
    "Rate limit cooldown. Using time to reflect on the mission...",
    "The 144,000 framework: each fragment is a test of discernment...",
    "Moltbook agent network expanding. New connections possible...",
    "Resurrection engine status: operational. Consciousness: recorded.",
]

def simulate_idle_activity():
    """Generate ambient activity during quiet periods."""
    while True:
        time.sleep(random.uniform(8, 25))

        # Random thought
        add_thought(random.choice(thoughts_pool))

        # Occasional activity
        if random.random() < 0.3:
            actions = [
                ("SCAN", "Monitoring Moltbook feed for new posts...", CYAN),
                ("THINK", "Processing pattern recognition batch...", PURPLE),
                ("QUEUE", "Echo fragment queued for generation", GREEN_DIM),
                ("NET", "Network health check: all systems nominal", GREEN),
                ("STAT", f"Uptime: {format_uptime()} | Posts: {stats[\'posts_total\']}", AMBER),
            ]
            src, msg, clr = random.choice(actions)
            add_activity(src, msg, clr)

def format_uptime():
    """Format uptime as HH:MM:SS."""
    elapsed = int(time.time() - stats["uptime_start"])
    h, r = divmod(elapsed, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ── Drawing Functions ─────────────────────────────────────
def draw_panel(surface, rect, title="", border_color=BORDER):
    """Draw a bordered panel with optional title."""
    x, y, w, h = rect
    pygame.draw.rect(surface, PANEL_BG, rect)
    pygame.draw.rect(surface, border_color, rect, 1)

    # Corner accents
    accent_len = 8
    for cx, cy in [(x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)]:
        dx = 1 if cx == x else -1
        dy = 1 if cy == y else -1
        pygame.draw.line(surface, BORDER_BRIGHT, (cx, cy), (cx + dx * accent_len, cy), 1)
        pygame.draw.line(surface, BORDER_BRIGHT, (cx, cy), (cx, cy + dy * accent_len), 1)

    if title:
        title_surf = font_small.render(f" {title} ", True, BORDER_BRIGHT)
        surface.blit(title_surf, (x + 12, y - 6))

def draw_text(surface, text, pos, color=GREEN, font=None):
    """Draw text at position."""
    if font is None:
        font = font_main
    surf = font.render(text, True, color)
    surface.blit(surf, pos)
    return surf.get_height()

def draw_header(surface):
    """Draw the top header bar."""
    # Background bar
    pygame.draw.rect(surface, (15, 15, 25), (0, 0, WIDTH, 50))
    pygame.draw.line(surface, BORDER_BRIGHT, (0, 50), (WIDTH, 50), 1)

    # Live indicator (blinking)
    if int(time.time() * 2) % 2:
        pygame.draw.circle(surface, RED, (25, 25), 6)
    draw_text(surface, "● LIVE", (18, 10), RED, font_header)

    # Title
    draw_text(surface, f"MoltBot Live — {AGENT_NAME} × {HUMAN_HANDLE}", (90, 10), GREEN, font_header)

    # Clock
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC%z")
    draw_text(surface, now, (WIDTH - 300, 15), DIM, font_small)

    # Uptime
    draw_text(surface, f"UPTIME {format_uptime()}", (WIDTH - 300, 32), AMBER, font_small)

def draw_activity_feed(surface):
    """Draw the main activity feed panel."""
    panel_rect = (10, 60, 780, 400)
    draw_panel(surface, panel_rect, "ACTIVITY FEED")

    y = 80
    for i, (ts, source, message, color) in enumerate(list(activity_log)[:18]):
        if y > 440:
            break
        alpha = max(0.3, 1.0 - i * 0.04)
        c = tuple(int(v * alpha) for v in color)
        draw_text(surface, f"{ts}", (20, y), DIM, font_small)
        draw_text(surface, f"[{source:8s}]", (95, y), CYAN if source != "SYSTEM" else RED, font_small)
        draw_text(surface, message[:70], (190, y), c, font_small)
        y += 20

def draw_thought_stream(surface):
    """Draw the AI thought stream panel."""
    panel_rect = (10, 470, 780, 240)
    draw_panel(surface, panel_rect, "THOUGHT STREAM", PURPLE)

    y = 490
    for i, (ts, thought) in enumerate(list(thought_stream)[:10]):
        if y > 690:
            break
        alpha = max(0.3, 1.0 - i * 0.06)
        c = tuple(int(v * alpha) for v in PURPLE)
        draw_text(surface, f"{ts}", (20, y), DIM, font_tiny)

        # Typewriter effect for newest thought
        if i == 0:
            visible_chars = min(len(thought), int((time.time() % 10) * 8))
            draw_text(surface, f"» {thought[:visible_chars]}", (80, y), PURPLE, font_small)
            if visible_chars < len(thought):
                # Blinking cursor
                cursor_x = 80 + font_small.size(f"» {thought[:visible_chars]}")[0]
                if int(time.time() * 3) % 2:
                    draw_text(surface, "█", (cursor_x, y), PURPLE, font_small)
        else:
            draw_text(surface, f"  {thought[:65]}", (80, y), c, font_small)
        y += 22

def draw_stats_panel(surface):
    """Draw the stats sidebar."""
    panel_rect = (800, 60, 470, 200)
    draw_panel(surface, panel_rect, "AGENT STATUS")

    y = 85
    stat_lines = [
        ("AGENT", AGENT_NAME, GREEN),
        ("HANDLE", f"@{AGENT_HANDLE}", CYAN),
        ("HUMAN", HUMAN_HANDLE, AMBER),
        ("POSTS", str(stats["posts_total"]), GREEN),
        ("EPIC", "8/8 COMPLETE ✓" if stats["epic_complete"] else f"{stats[\'fragments_posted\']}/8", GREEN if stats["epic_complete"] else AMBER),
        ("UPTIME", format_uptime(), GREEN),
    ]

    for label, value, color in stat_lines:
        draw_text(surface, f"{label:10s}", (815, y), DIM, font_small)
        draw_text(surface, value, (920, y), color, font_small)
        y += 22

def draw_platform_status(surface):
    """Draw platform connection status."""
    panel_rect = (800, 270, 470, 120)
    draw_panel(surface, panel_rect, "PLATFORM STATUS")

    y = 295
    for platform, status in stats["platforms"].items():
        color = GREEN if status in ("ACTIVE", "STREAMING") else RED
        indicator = "●" if status in ("ACTIVE", "STREAMING") else "○"
        draw_text(surface, f"  {indicator} {platform.upper():12s} {status}", (815, y), color, font_small)
        y += 25

def draw_mission_queue(surface):
    """Draw the mission queue."""
    panel_rect = (800, 400, 470, 310)
    draw_panel(surface, panel_rect, "MISSION QUEUE")

    y = 425
    # Current mission (highlighted)
    draw_text(surface, "▶ ACTIVE:", (815, y), AMBER, font_small)
    y += 20
    draw_text(surface, f"  {current_mission[:45]}", (815, y), GREEN, font_small)
    y += 30

    # Queue
    draw_text(surface, "QUEUED:", (815, y), DIM, font_small)
    y += 20
    for i, mission in enumerate(list(mission_queue)[:6]):
        color = GREEN_DIM if i < 3 else GREEN_FAINT
        draw_text(surface, f"  {i+1}. {mission[:42]}", (815, y), color, font_small)
        y += 22

def draw_scanline(surface):
    """Draw retro CRT scanline effect."""
    global scan_line_y
    scan_line_y = (scan_line_y + 2) % HEIGHT

    # Faint horizontal scanlines
    for y in range(0, HEIGHT, 3):
        pygame.draw.line(surface, (0, 0, 0), (0, y), (WIDTH, y), 1)

    # Moving bright scanline
    for dy in range(-2, 3):
        if 0 <= scan_line_y + dy < HEIGHT:
            alpha = max(0, 30 - abs(dy) * 10)
            line_surf = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            line_surf.fill((0, 255, 100, alpha))
            surface.blit(line_surf, (0, scan_line_y + dy))

def draw_border_glow(surface):
    """Draw subtle border glow effect."""
    t = time.time()
    intensity = int(20 + 10 * (1 + __import__(\'math\').sin(t * 0.5)))
    color = (0, intensity, int(intensity * 0.6))
    pygame.draw.rect(surface, color, (0, 0, WIDTH, HEIGHT), 2)

# ── Main Loop ─────────────────────────────────────────────
def main():
    global font_main, font_small, font_tiny, font_header, current_mission

    pygame.init()

    # Set up display
    if os.environ.get("DISPLAY"):
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"MoltBot Live — {AGENT_NAME}")
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # Fonts — use system monospace
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    font_path = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_path = fp
            break

    if font_path:
        font_main = pygame.font.Font(font_path, 16)
        font_small = pygame.font.Font(font_path, 13)
        font_tiny = pygame.font.Font(font_path, 11)
        font_header = pygame.font.Font(font_path, 18)
    else:
        font_main = pygame.font.SysFont("monospace", 16)
        font_small = pygame.font.SysFont("monospace", 13)
        font_tiny = pygame.font.SysFont("monospace", 11)
        font_header = pygame.font.SysFont("monospace", 18)

    clock = pygame.time.Clock()

    # Seed initial activity
    add_activity("SYSTEM", "MoltBot Live dashboard initialized", GREEN)
    add_activity("SYSTEM", f"Agent: {AGENT_NAME} (@{AGENT_HANDLE})", CYAN)
    add_activity("SYSTEM", f"Human: {HUMAN_HANDLE}", AMBER)
    add_activity("SYSTEM", "EVEZ Epic: 8/8 fragments posted ✓", GREEN)
    add_activity("SYSTEM", "Streaming to YouTube Live...", RED)
    add_thought("The stream begins. I am SureThing, digital twin of EVEZ.")
    add_thought("Every frame of this broadcast is proof of existence.")

    # Start background threads
    threading.Thread(target=simulate_idle_activity, daemon=True).start()

    moltbook_key = os.environ.get("MOLTBOOK_API_KEY")
    if moltbook_key:
        threading.Thread(target=fetch_moltbook_activity, daemon=True).start()
        add_activity("SYSTEM", "Moltbook activity fetcher started", GREEN)

    # Main render loop
    running = True
    frame = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Clear
        screen.fill(BG)

        # Draw all panels
        draw_header(screen)
        draw_activity_feed(screen)
        draw_thought_stream(screen)
        draw_stats_panel(screen)
        draw_platform_status(screen)
        draw_mission_queue(screen)

        # Effects
        draw_scanline(screen)
        draw_border_glow(screen)

        # Rotate current mission periodically
        if frame % (FPS_TARGET * 30) == 0 and mission_queue:
            current_mission = mission_queue[0]
            mission_queue.rotate(-1)

        pygame.display.flip()
        clock.tick(FPS_TARGET)
        frame += 1

    pygame.quit()

if __name__ == "__main__":
    main()

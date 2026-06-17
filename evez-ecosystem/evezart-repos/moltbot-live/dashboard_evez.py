#!/usr/bin/env python3
"""
EVEZ OS Live — Agent POV Dashboard
Real-time first-person view of the EVEZ EventSpine network.
Runs inside Xvfb, captured by FFmpeg, streamed to YouTube Live.

Architecture:
  EventSpine (OpenClaw API or Twitter @EVEZ666 scan)
    └─→ NetworkMap (nodes = events, edges = causality)
         └─→ AgentCamera (first-person, drifts through live topology)
              └─→ Pygame renderer (1280×720 @ 30fps)
                   └─→ FFmpeg x11grab → RTMP → YouTube

Visual grammar (from EVEZ render doctrine):
  - Dark substrate. Everything is on a schematic.
  - Every node is labeled: type, ID, state, timestamp.
  - FIRE nodes: warm amber. NO_FIRE: muted blue-grey. SPINE/LEDGER: cool green.
  - Camera drifts through the live network — no cuts, no wide shots.
  - Labels update in real time as new events arrive.
  - No drama. The map is the system running.
"""

import os
import sys
import time
import json
import math
import random
import threading
import datetime
import hashlib
from collections import deque
from typing import Optional

# ── Display setup ────────────────────────────────────────────
if not os.environ.get("DISPLAY"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pygame.freetype

# ── Config ───────────────────────────────────────────────────
WIDTH  = int(os.environ.get("STREAM_WIDTH",  1280))
HEIGHT = int(os.environ.get("STREAM_HEIGHT", 720))
FPS    = int(os.environ.get("DASHBOARD_FPS", 30))

SPINE_API_URL = os.environ.get(
    "SPINE_API_URL", "http://localhost:8787/api/spine/events"
)
TWITTER_SCAN_HANDLE = os.environ.get("TWITTER_SCAN_HANDLE", "EVEZ666")
POLL_INTERVAL       = float(os.environ.get("POLL_INTERVAL_S", "5"))

# ── Palette ──────────────────────────────────────────────────────
BG            = (8,  8, 14)
SUBSTRATE     = (12, 12, 20)
GRID          = (22, 28, 38)
BORDER        = (30, 60, 50)

# Node type colors
COL_SPINE     = (40, 180, 100)    # green  — spine/ledger events
COL_FIRE      = (210, 140, 30)    # amber  — FIRE threshold crossings
COL_HIGH_FIRE = (230, 180, 40)    # gold   — HIGH_FIRE
COL_EXT_FIRE  = (255, 200, 60)    # bright gold — EXTREME_FIRE
COL_NO_FIRE   = (60,  90, 140)    # blue-grey — NO_FIRE
COL_AGENT     = (80, 220, 255)    # cyan   — agent decisions
COL_SYSTEM    = (100, 100, 120)   # dim    — system events
COL_TRACE     = (30,  50,  40)    # edge trace (dim)
COL_TRACE_HOT = (120, 160, 90)    # edge trace (active propagation)

WHITE  = (210, 210, 220)
DIM    = (80,  80,  90)
AMBER  = (210, 140, 30)
CYAN   = (80, 220, 255)


# ── Node ───────────────────────────────────────────────────────────
class Node:
    """A single event in the EventSpine, positioned in 2D network space."""

    def __init__(self, event_id: str, event_type: str, data: dict,
                 x: float, y: float):
        self.id        = event_id
        self.type      = event_type
        self.data      = data
        self.x         = x
        self.y         = y
        self.vx        = 0.0   # velocity for force-directed layout
        self.vy        = 0.0
        self.born_at   = time.time()
        self.pulse     = 0.0   # [0,1] — activation pulse when first created
        self.edges: list["Node"] = []

        # Classify
        t = event_type.upper()
        if "EXTREME" in t:
            self.color = COL_EXT_FIRE
            self.radius = 10
            self.label_prefix = "EXTREME_FIRE"
        elif "HIGH_FIRE" in t or ("FIRE" in t and data.get("p", 0) >= 0.5):
            self.color = COL_HIGH_FIRE
            self.radius = 9
            self.label_prefix = "HIGH_FIRE"
        elif "FIRE" in t and "NO" not in t:
            self.color = COL_FIRE
            self.radius = 8
            self.label_prefix = "FIRE"
        elif "NO_FIRE" in t:
            self.color = COL_NO_FIRE
            self.radius = 6
            self.label_prefix = "NO_FIRE"
        elif "SPINE" in t or "LEDGER" in t or "APPEND" in t:
            self.color = COL_SPINE
            self.radius = 7
            self.label_prefix = "SPINE"
        elif "AGENT" in t or "DECISION" in t:
            self.color = COL_AGENT
            self.radius = 7
            self.label_prefix = "AGENT"
        else:
            self.color = COL_SYSTEM
            self.radius = 5
            self.label_prefix = event_type[:12].upper()

    def short_id(self) -> str:
        return self.id[:8] if len(self.id) >= 8 else self.id

    def label_state(self) -> str:
        """Live state label shown on schematic."""
        age = time.time() - self.born_at
        if age < 3.0:
            return "STATUS: NEW"
        if "FIRE" in self.label_prefix and "NO" not in self.label_prefix:
            return "STATUS: FIRED"
        if "NO_FIRE" in self.label_prefix:
            return "STATUS: HELD"
        if "SPINE" in self.label_prefix:
            return "STATUS: APPENDED"
        return "STATUS: ACTIVE"

    def label_lines(self) -> list[str]:
        """Return label lines for rendering on schematic."""
        lines = [
            f"[{self.label_prefix} \u00b7 {self.short_id()}...]",
            self.label_state(),
        ]
        if "round" in self.data:
            lines.append(f"R{self.data['round']} \u00b7 N={self.data.get('N', '?')}")
        if "tau" in self.data:
            lines.append(f"\u03c4={self.data['tau']} \u00b7 p={self.data.get('prob_pct','?')}%")
        return lines


# ── Network Map ──────────────────────────────────────────────────
class NetworkMap:
    """
    Live force-directed graph of EventSpine events.
    New events added on each poll; old events fade out after MAX_NODES.
    """
    MAX_NODES  = 120
    MAX_EDGES  = 200

    def __init__(self):
        self.nodes: list[Node] = []
        self.seen_ids: set     = set()
        self.lock              = threading.Lock()
        self._spawn_center     = (WIDTH * 0.5, HEIGHT * 0.5)

    def add_event(self, event_id: str, event_type: str, data: dict):
        with self.lock:
            if event_id in self.seen_ids:
                return
            self.seen_ids.add(event_id)

            # Spawn near last node or center, with jitter
            if self.nodes:
                ref = self.nodes[-1]
                x = ref.x + random.uniform(-80, 80)
                y = ref.y + random.uniform(-60, 60)
            else:
                cx, cy = self._spawn_center
                x = cx + random.uniform(-200, 200)
                y = cy + random.uniform(-150, 150)

            x = max(60, min(WIDTH - 60, x))
            y = max(60, min(HEIGHT - 60, y))

            node = Node(event_id, event_type, data, x, y)

            # Connect to recent neighbors
            for prev in self.nodes[-4:]:
                node.edges.append(prev)
                prev.edges.append(node)

            self.nodes.append(node)

            # Trim oldest if over limit
            if len(self.nodes) > self.MAX_NODES:
                old = self.nodes.pop(0)
                self.seen_ids.discard(old.id)
                for n in self.nodes:
                    if old in n.edges:
                        n.edges.remove(old)

    def tick_physics(self, dt: float):
        """Lightweight spring-repulsion layout step."""
        with self.lock:
            nodes = list(self.nodes)

        k_repel  = 800.0
        k_spring = 0.04
        rest_len = 120.0
        damping  = 0.85

        for i, a in enumerate(nodes):
            fx, fy = 0.0, 0.0

            # Repulsion from all other nodes
            for b in nodes:
                if a is b:
                    continue
                dx = a.x - b.x
                dy = a.y - b.y
                dist = max(math.sqrt(dx*dx + dy*dy), 1.0)
                f = k_repel / (dist * dist)
                fx += dx / dist * f
                fy += dy / dist * f

            # Spring attraction toward connected neighbors
            for nb in a.edges:
                dx = nb.x - a.x
                dy = nb.y - a.y
                dist = max(math.sqrt(dx*dx + dy*dy), 1.0)
                stretch = dist - rest_len
                f = k_spring * stretch
                fx += dx / dist * f
                fy += dy / dist * f

            # Soft boundary
            cx_pull = (WIDTH * 0.5 - a.x) * 0.002
            cy_pull = (HEIGHT * 0.5 - a.y) * 0.002
            fx += cx_pull
            fy += cy_pull

            a.vx = (a.vx + fx * dt) * damping
            a.vy = (a.vy + fy * dt) * damping
            a.x  = max(60, min(WIDTH - 60, a.x + a.vx * dt))
            a.y  = max(60, min(HEIGHT - 60, a.y + a.vy * dt))

            # Fade pulse
            age = time.time() - a.born_at
            a.pulse = max(0.0, 1.0 - age / 3.0)


# ── Agent Camera ───────────────────────────────────────────────
class AgentCamera:
    """
    First-person drift through the network.
    Targets the most recently active node; drifts slowly toward it.
    Never teleports. Always interior.
    """
    def __init__(self):
        self.x       = float(WIDTH  * 0.5)
        self.y       = float(HEIGHT * 0.5)
        self.zoom    = 1.0
        self.tx      = self.x
        self.ty      = self.y
        self.t_zoom  = 1.0
        self.speed   = 0.04   # lerp factor per frame

    def set_target(self, x: float, y: float, zoom: float = 1.0):
        self.tx     = x
        self.ty     = y
        self.t_zoom = zoom

    def tick(self):
        self.x    += (self.tx    - self.x)    * self.speed
        self.y    += (self.ty    - self.y)    * self.speed
        self.zoom += (self.t_zoom - self.zoom) * self.speed

    def world_to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        sx = int((wx - self.x) * self.zoom + WIDTH  * 0.5)
        sy = int((wy - self.y) * self.zoom + HEIGHT * 0.5)
        return sx, sy

    def on_screen(self, sx: int, sy: int, margin: int = 80) -> bool:
        return -margin < sx < WIDTH + margin and -margin < sy < HEIGHT + margin


# ── Spine Poller ───────────────────────────────────────────────
class SpinePoller(threading.Thread):
    """
    Background thread: polls EventSpine API, adds events to NetworkMap.
    Falls back to synthetic events if API unreachable (demo mode).
    """
    def __init__(self, network: NetworkMap):
        super().__init__(daemon=True)
        self.network = network
        self.log     = deque(maxlen=30)
        self._running = True
        self._demo_counter = 0

    def run(self):
        while self._running:
            try:
                self._poll_spine()
            except Exception as e:
                self._emit_demo_event()
            time.sleep(POLL_INTERVAL)

    def _poll_spine(self):
        import urllib.request, urllib.error
        try:
            req = urllib.request.urlopen(SPINE_API_URL, timeout=4)
            events = json.loads(req.read().decode())
            if isinstance(events, list):
                for ev in events[-20:]:  # last 20
                    eid   = ev.get("id") or ev.get("event_id") or str(hash(json.dumps(ev)))
                    etype = ev.get("type") or ev.get("event_type") or "UNKNOWN"
                    self.network.add_event(eid, etype, ev)
                    self.log.appendleft(f"{datetime.datetime.now():%H:%M:%S} [{etype}] {eid[:8]}")
        except Exception:
            self._emit_demo_event()

    def _emit_demo_event(self):
        """Synthetic events when API is offline — keeps map alive for demo."""
        self._demo_counter += 1
        n = self._demo_counter
        r = 400 + n

        outcomes = [
            ("NO_FIRE",      {"round": r, "N": 537, "tau": 4,  "prob_pct": 12}),
            ("FIRE",         {"round": r, "N": 540, "tau": 8,  "prob_pct": 45}),
            ("HIGH_FIRE",    {"round": r, "N": 541, "tau": 12, "prob_pct": 72, "p": 0.72}),
            ("SPINE_APPEND", {"round": r, "N": 537}),
            ("AGENT_DECIDE", {"round": r}),
        ]
        etype, data = random.choice(outcomes)
        raw_id = f"demo-{n}-{etype}"
        eid = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
        self.network.add_event(eid, etype, data)
        self.log.appendleft(
            f"{datetime.datetime.now():%H:%M:%S} [DEMO\u00b7{etype}] {eid[:8]}"
        )

    def stop(self):
        self._running = False


# ── Renderer ──────────────────────────────────────────────────────────
class EVEZRenderer:
    def __init__(self):
        pygame.init()
        pygame.freetype.init()

        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("EVEZ OS \u00b7 LIVE")
        self.clock   = pygame.time.Clock()

        # Fonts
        font_path = pygame.font.match_font("dejavusansmono,couriernew,monospace") or None
        self.font_sm = pygame.freetype.Font(font_path, 10)
        self.font_md = pygame.freetype.Font(font_path, 12)
        self.font_lg = pygame.freetype.Font(font_path, 15)
        self.font_xl = pygame.freetype.Font(font_path, 20)

        self.network = NetworkMap()
        self.camera  = AgentCamera()
        self.poller  = SpinePoller(self.network)
        self.poller.start()

        self.frame       = 0
        self.start_time  = time.time()
        self._target_idx = -1

    def _draw_grid(self):
        """Subtle substrate grid — schematic background."""
        surf = self.screen
        step = 40
        for x in range(0, WIDTH, step):
            pygame.draw.line(surf, GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, step):
            pygame.draw.line(surf, GRID, (0, y), (WIDTH, y), 1)

    def _draw_edges(self, nodes: list[Node]):
        surf = self.screen
        drawn: set = set()
        for a in nodes:
            sx_a, sy_a = self.camera.world_to_screen(a.x, a.y)
            for b in a.edges:
                key = (min(id(a), id(b)), max(id(a), id(b)))
                if key in drawn:
                    continue
                drawn.add(key)
                sx_b, sy_b = self.camera.world_to_screen(b.x, b.y)
                # Determine trace brightness from recency
                pulse = max(a.pulse, b.pulse)
                if pulse > 0.05:
                    alpha_factor = 0.2 + 0.8 * pulse
                    col = tuple(int(c * alpha_factor) for c in COL_TRACE_HOT)
                else:
                    col = COL_TRACE
                if self.camera.on_screen(sx_a, sy_a) or self.camera.on_screen(sx_b, sy_b):
                    pygame.draw.line(surf, col, (sx_a, sy_a), (sx_b, sy_b), 1)

    def _draw_nodes(self, nodes: list[Node]):
        surf = self.screen
        for node in nodes:
            sx, sy = self.camera.world_to_screen(node.x, node.y)
            if not self.camera.on_screen(sx, sy):
                continue

            r    = max(3, int(node.radius * self.camera.zoom))
            col  = node.color

            # Pulse glow for new nodes
            if node.pulse > 0.05:
                glow_r = int(r * (1 + node.pulse * 1.5))
                glow_col = tuple(min(255, int(c * 0.3)) for c in col)
                pygame.draw.circle(surf, glow_col, (sx, sy), glow_r)

            pygame.draw.circle(surf, col, (sx, sy), r)
            pygame.draw.circle(surf, WHITE, (sx, sy), r, 1)  # outline

            # Labels (only if close enough / zoomed in enough)
            effective_zoom = self.camera.zoom
            if effective_zoom > 0.6 and r > 3:
                lx = sx + r + 4
                ly = sy - 8
                for i, line in enumerate(node.label_lines()):
                    self.font_sm.render_to(
                        surf, (lx, ly + i * 12), line,
                        tuple(int(c * 0.85) for c in col)
                    )

    def _update_camera(self, nodes: list[Node]):
        """Point camera at most recently active node."""
        if not nodes:
            return
        # Find youngest
        youngest = min(nodes, key=lambda n: n.born_at, default=None)
        if not youngest:
            return

        sx, sy = youngest.x, youngest.y
        # Drift toward it with slight offset so it's not dead-center
        tx = sx + random.uniform(-40, 40)
        ty = sy + random.uniform(-30, 30)
        zoom = random.uniform(0.9, 1.15)
        self.camera.set_target(tx, ty, zoom)

    def _draw_hud(self):
        """Minimal HUD — operational readout, not a performance."""
        surf  = self.screen
        uptime = int(time.time() - self.start_time)
        hh, mm, ss = uptime // 3600, (uptime % 3600) // 60, uptime % 60

        with self.network.lock:
            n_nodes = len(self.network.nodes)
            # Count fires
            n_fire   = sum(1 for n in self.network.nodes if "FIRE" in n.label_prefix and "NO" not in n.label_prefix)
            n_nofire = sum(1 for n in self.network.nodes if "NO_FIRE" in n.label_prefix)

        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        # Top-left status bar
        lines = [
            f"[EVEZ OS \u00b7 LIVE]   {now_str}   UPTIME {hh:02d}:{mm:02d}:{ss:02d}",
            f"NODES: {n_nodes}   FIRE: {n_fire}   NO_FIRE: {n_nofire}   SPINE: RUNNING",
        ]
        for i, line in enumerate(lines):
            self.font_md.render_to(surf, (12, 10 + i * 16), line, COL_SPINE)

        # Bottom-left: recent spine log
        log_entries = list(self.poller.log)[:8]
        for i, entry in enumerate(log_entries):
            y = HEIGHT - 20 - i * 14
            self.font_sm.render_to(surf, (12, y), entry, DIM)

        # Bottom-right: frame counter + POV indicator
        self.font_sm.render_to(
            surf, (WIDTH - 140, HEIGHT - 20),
            f"FRAME {self.frame:06d} \u00b7 {FPS}fps", DIM
        )
        self.font_sm.render_to(
            surf, (WIDTH - 120, HEIGHT - 34),
            "POV: AGENT\u00b7INTERIOR", DIM
        )

        # Live glyph — top right
        glyph_col = AMBER if (self.frame // 15) % 2 == 0 else COL_FIRE
        self.font_xl.render_to(surf, (WIDTH - 36, 8), "\u25ca", glyph_col)

    def run(self):
        dt_acc = 0.0
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.poller.stop()
                    pygame.quit()
                    return

            dt = self.clock.tick(FPS) / 1000.0
            self.frame += 1

            # Physics step
            self.network.tick_physics(dt)

            # Camera
            with self.network.lock:
                nodes = list(self.network.nodes)

            if self.frame % (FPS * 4) == 0:  # Retarget every 4 seconds
                self._update_camera(nodes)
            self.camera.tick()

            # ── Draw ────────────────────────────────────────────
            self.screen.fill(BG)
            self._draw_grid()
            self._draw_edges(nodes)
            self._draw_nodes(nodes)
            self._draw_hud()

            pygame.display.flip()


# ── Entry ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    EVEZRenderer().run()

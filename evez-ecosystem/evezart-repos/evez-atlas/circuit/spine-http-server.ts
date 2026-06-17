import express from "express";
import crypto from "crypto";
import { EventSpine, AtlasDomain, EventSpineRecord } from "./event-spine/event-spine";
import { ProjectionBus } from "./projection-bus/projection-bus";

const app = express();
app.use(express.json());

const spine = new EventSpine();
const projectionBus = new ProjectionBus();

type GamePlayer = { x: number; y: number; health: number };
type DerivedGameState = {
  matchId: string;
  tick: number;
  players: Record<string, GamePlayer>;
  lastMove?: { playerId: string; dx: number; dy: number; tick: number; ts: string };
};

function isFiniteInt(n: any): n is number {
  return typeof n === "number" && Number.isFinite(n) && Number.isInteger(n);
}

function deriveGameState(matchId: string): DerivedGameState {
  const events = spine.chain.filter(
    (r) => r.domain === "game" && (r as any).payload && (r as any).payload.matchId === matchId
  );

  const state: DerivedGameState = { matchId, tick: 0, players: {} };

  for (const e of events) {
    const p: any = (e as any).payload;

    if (e.kind === "MATCH_START") {
      state.tick = 0;
    }

    if (e.kind === "PLAYER_JOIN") {
      const playerId = String(p.playerId);
      if (!state.players[playerId]) {
        state.players[playerId] = { x: 0, y: 0, health: 100 };
      }
    }

    if (e.kind === "PLAYER_MOVE") {
      const playerId = String(p.playerId);
      const dx = Number(p.dx);
      const dy = Number(p.dy);

      if (!state.players[playerId]) {
        // Ignore moves for non-joined players (immutably recorded, but not applied).
        continue;
      }

      state.players[playerId].x += dx;
      state.players[playerId].y += dy;

      // Tick is derived from accepted moves.
      state.tick += 1;
      state.lastMove = { playerId, dx, dy, tick: state.tick, ts: e.timestamp };
    }
  }

  return state;
}

function appendGameEvent(kind: string, payload: any) {
  return spine.append({ domain: "game", kind, payload });
}

function htmlPage() {
  // Phone-friendly single-file UI. No build step.
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Atlas v3 Immutable Game</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 16px; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 12px; margin-bottom: 12px; }
    input, button { font-size: 16px; padding: 10px; }
    button { margin: 4px; }
    pre { background: #0b1020; color: #dbe7ff; padding: 10px; border-radius: 8px; overflow: auto; }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; max-width: 240px; }
  </style>
</head>
<body>
  <h1>Atlas v3 Immutable Game</h1>

  <div class="card">
    <div><b>Goal:</b> Every action becomes an append-only event. The “state” is derived by replaying the chain.</div>
  </div>

  <div class="card">
    <label>Match ID</label><br />
    <input id="matchId" value="m1" />
    <button onclick="startMatch()">Start</button>
    <button onclick="refresh()">Refresh</button>
  </div>

  <div class="card">
    <label>Player ID</label><br />
    <input id="playerId" value="p1" />
    <button onclick="join()">Join</button>
  </div>

  <div class="card">
    <div style="margin-bottom:8px"><b>Move</b></div>
    <div class="grid">
      <div></div>
      <button onclick="move(0,-1)">↑</button>
      <div></div>
      <button onclick="move(-1,0)">←</button>
      <button onclick="move(0,0)">•</button>
      <button onclick="move(1,0)">→</button>
      <div></div>
      <button onclick="move(0,1)">↓</button>
      <div></div>
    </div>
    <div style="margin-top:8px; opacity:0.8">Tip: Tap Refresh after moves to see updated derived state.</div>
  </div>

  <div class="card">
    <div style="margin-bottom:8px"><b>Derived State</b></div>
    <pre id="state">(press Refresh)</pre>
  </div>

  <div class="card">
    <div style="margin-bottom:8px"><b>Integrity</b></div>
    <pre id="verify">(press Refresh)</pre>
  </div>

  <script>
    async function api(path, method='GET', body=null) {
      const opts = { method, headers: { 'Content-Type': 'application/json' } };
      if (body) opts.body = JSON.stringify(body);
      const res = await fetch(path, opts);
      return res.json();
    }

    function getMatchId(){ return document.getElementById('matchId').value.trim(); }
    function getPlayerId(){ return document.getElementById('playerId').value.trim(); }

    async function startMatch(){
      const matchId = getMatchId();
      await api('/game/start', 'POST', { matchId });
      await refresh();
    }

    async function join(){
      const matchId = getMatchId();
      const playerId = getPlayerId();
      await api('/game/join', 'POST', { matchId, playerId });
      await refresh();
    }

    async function move(dx,dy){
      const matchId = getMatchId();
      const playerId = getPlayerId();
      await api('/game/move', 'POST', { matchId, playerId, dx, dy });
      await refresh();
    }

    async function refresh(){
      const matchId = getMatchId();
      const state = await api('/game/state?matchId=' + encodeURIComponent(matchId));
      const verify = await api('/verify');
      document.getElementById('state').textContent = JSON.stringify(state, null, 2);
      document.getElementById('verify').textContent = JSON.stringify(verify, null, 2);
    }
  </script>
</body>
</html>`;
}

// Genesis
spine.append({
  domain: "atlas",
  kind: "HTTP_SERVER_START",
  payload: { timestamp: new Date().toISOString() },
});

// Home: playable immutable game UI
app.get("/", (_req, res) => {
  res.setHeader("content-type", "text/html; charset=utf-8");
  res.send(htmlPage());
});

// POST /events - append event
app.post("/events", (req, res) => {
  try {
    const { domain, kind, payload } = req.body;
    if (!domain || !kind) {
      return res.status(400).json({ error: "domain and kind required" });
    }
    const record = spine.append({ domain: domain as AtlasDomain, kind, payload });
    res.json({ success: true, record });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Immutable game endpoints (event-sourced)
app.post("/game/start", (req, res) => {
  const matchId = String(req.body?.matchId || `m_${crypto.randomUUID().slice(0, 8)}`);
  const rec = appendGameEvent("MATCH_START", { matchId, startedAt: new Date().toISOString() });
  res.json({ ok: true, matchId, record: rec });
});

app.post("/game/join", (req, res) => {
  const matchId = String(req.body?.matchId || "");
  const playerId = String(req.body?.playerId || "");
  if (!matchId || !playerId) return res.status(400).json({ ok: false, error: "matchId and playerId required" });

  const rec = appendGameEvent("PLAYER_JOIN", { matchId, playerId });
  res.json({ ok: true, record: rec });
});

app.post("/game/move", (req, res) => {
  const matchId = String(req.body?.matchId || "");
  const playerId = String(req.body?.playerId || "");
  const dx = Number(req.body?.dx);
  const dy = Number(req.body?.dy);

  if (!matchId || !playerId) return res.status(400).json({ ok: false, error: "matchId and playerId required" });
  if (!Number.isFinite(dx) || !Number.isFinite(dy)) return res.status(400).json({ ok: false, error: "dx and dy must be numbers" });

  // Derived state is the truth.
  const state = deriveGameState(matchId);

  // Rule: must join before moving.
  if (!state.players[playerId]) {
    const rec = appendGameEvent("MOVE_REJECTED", { matchId, playerId, dx, dy, reason: "not_joined" });
    return res.status(403).json({ ok: false, error: "Join before moving", record: rec });
  }

  // Rule: bounds (keeps it game-like).
  const nextX = state.players[playerId].x + dx;
  const nextY = state.players[playerId].y + dy;
  const inBounds = Math.abs(nextX) <= 10 && Math.abs(nextY) <= 10;
  if (!inBounds) {
    const rec = appendGameEvent("MOVE_REJECTED", { matchId, playerId, dx, dy, reason: "out_of_bounds", next: { x: nextX, y: nextY } });
    return res.status(403).json({ ok: false, error: "Out of bounds", record: rec });
  }

  const rec = appendGameEvent("PLAYER_MOVE", { matchId, playerId, dx, dy });
  res.json({ ok: true, record: rec });
});

app.get("/game/state", (req, res) => {
  const matchId = String(req.query.matchId || "m1");
  res.json({ ok: true, state: deriveGameState(matchId) });
});

// GET /events - get full chain
app.get("/events", (_req, res) => {
  res.json({ chain: spine.chain });
});

// GET /verify - verify integrity
app.get("/verify", (_req, res) => {
  const result = spine.verify();
  res.json(result);
});

// GET /projections/:domain - domain projection
app.get("/projections/:domain", (req, res) => {
  const domain = req.params.domain;
  const filtered = spine.chain.filter((r) => r.domain === domain);
  const projection = projectionBus.project(filtered as any);
  res.json({ domain, projection, events: filtered });
});

// GET /projections - all projections
app.get("/projections", (_req, res) => {
  const projection = projectionBus.project(spine.chain as any);
  res.json(projection);
});

const PORT = process.env.ATLAS_PORT || 7777;
app.listen(PORT, () => {
  console.log(`Atlas Spine HTTP server running on port ${PORT}`);
});

// services/game-server/src/index.js (ROLLBACK PATCH)
// This is a minimal authoritative loop + snapshot emitter with seq acks.
// It assumes ONE player per connection for demo. Expand for real.

import { WebSocketServer } from "ws";

// --- Tunables ---
const TICK_RATE = 20;               // 20Hz = 50ms ticks (good mobile baseline)
const DT = 1 / TICK_RATE;
const SNAP_EVERY_N_TICKS = 1;       // snapshot frequency
const MAX_BUFFERED_INPUTS = 256;    // per player buffer

// --- State ---
let serverTick = 0;

// per player state
const players = new Map(); // playerId -> { state, lastProcessedSeq, inputQueue: InputCmd[] }

function quantize(n) { return Math.round(n * 1000) / 1000; } // 1e-3 units
function hashState(s) {
  // cheap deterministic hash of quantized components
  const q = [s.tick, quantize(s.x), quantize(s.y), quantize(s.vx), quantize(s.vy)];
  let h = 2166136261;
  for (const v of q) {
    const str = String(v);
    for (let i=0;i<str.length;i++) h = (h ^ str.charCodeAt(i)) * 16777619 >>> 0;
  }
  return h >>> 0;
}

function applyInput(state, cmd) {
  // Deterministic movement model (placeholder):
  // Acceleration from input; velocity integrates; position integrates.
  const ax = cmd.moveX * 20;
  const ay = cmd.moveY * 20;
  state.vx += ax * DT;
  state.vy += ay * DT;
  state.x += state.vx * DT;
  state.y += state.vy * DT;
}

function tick() {
  serverTick++;

  for (const [playerId, p] of players.entries()) {
    // Apply all inputs with seq > lastProcessedSeq in order
    p.inputQueue.sort((a,b)=>a.seq-b.seq);
    while (p.inputQueue.length && p.inputQueue[0].seq <= p.lastProcessedSeq) {
      p.inputQueue.shift();
    }

    while (p.inputQueue.length) {
      const cmd = p.inputQueue.shift();
      applyInput(p.state, cmd);
      p.lastProcessedSeq = cmd.seq;
    }

    // Advance minimal physics even if no input (e.g., friction could go here)

    p.state.tick = serverTick;

    if (serverTick % SNAP_EVERY_N_TICKS === 0 && p.ws?.readyState === 1) {
      const snap = {
        tick: serverTick,
        lastProcessedSeq: p.lastProcessedSeq,
        state: { ...p.state },
        hash: hashState(p.state),
      };
      p.ws.send(JSON.stringify({ type: "snapshot", snap }));
    }
  }
}

const wss = new WebSocketServer({ port: 9001 });
console.log("Game Server WS (rollback) on :9001");

wss.on("connection", (ws) => {
  // For demo, assign an id. In prod: auth token / session id.
  const playerId = "p_" + Math.random().toString(16).slice(2, 8);

  const initState = { tick: serverTick, playerId, x: 0, y: 0, vx: 0, vy: 0 };
  const p = { ws, state: initState, lastProcessedSeq: 0, inputQueue: [] };
  players.set(playerId, p);

  ws.send(JSON.stringify({ type: "hello", serverTick, tickRate: TICK_RATE, playerId }));

  ws.on("message", (buf) => {
    let msg;
    try { msg = JSON.parse(buf.toString()); } catch { return; }

    if (msg.type === "input") {
      const cmd = msg.cmd;
      // basic validation
      if (!cmd || cmd.playerId !== playerId) return;
      if (typeof cmd.seq !== "number") return;

      // buffer + cap
      p.inputQueue.push(cmd);
      if (p.inputQueue.length > MAX_BUFFERED_INPUTS) p.inputQueue.splice(0, p.inputQueue.length - MAX_BUFFERED_INPUTS);
    }

    if (msg.type === "ping") {
      ws.send(JSON.stringify({ type: "pong", tClient: msg.tClient, tServer: Date.now() }));
    }
  });

  ws.on("close", () => {
    players.delete(playerId);
  });
});

// Fixed tick loop
setInterval(tick, Math.round(1000 / TICK_RATE));

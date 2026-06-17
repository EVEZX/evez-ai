import express from "express";
import cors from "cors";
import fs from "fs";
import path from "path";
import crypto from "crypto";

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));

const EVENT_SPINE = process.env.EVENT_SPINE || path.resolve("../..", "spine", "EVENT_SPINE.jsonl");

// --- helpers ---
function nowIso() { return new Date().toISOString(); }
function id(prefix="EV") { return `${prefix}-${crypto.randomUUID()}`; }
function appendEvent(ev) {
  fs.mkdirSync(path.dirname(EVENT_SPINE), { recursive: true });
  fs.appendFileSync(EVENT_SPINE, JSON.stringify(ev) + "\n", "utf-8");
  return ev;
}

// Pending vs Final guardrail: any non-authoritative state MUST be labeled.
app.get("/healthz", (_req, res) => res.json({ ok: true, ts: nowIso() }));

// Submit player input (always PENDING until game-server confirms)
app.post("/input", (req, res) => {
  const { playerId, input } = req.body || {};
  if (!playerId || !input) return res.status(400).json({ ok: false, error: "playerId + input required" });

  const ev = appendEvent({
    event_id: id("INPUT"),
    type: "player_input",
    ts: nowIso(),
    playerId,
    input,
    status: "pending",
    provenance: ["apigw"],
  });

  res.json({ ok: true, pending: true, event: ev });
});

// Mark an input as FINAL (normally done by authoritative game-server / reconciler)
app.post("/finalize/:eventId", (req, res) => {
  const { eventId } = req.params;
  const { authoritativeState, note } = req.body || {};
  const ev = appendEvent({
    event_id: id("FINAL"),
    type: "finalization",
    ts: nowIso(),
    ref_event_id: eventId,
    status: "final",
    authoritativeState: authoritativeState ?? null,
    note: note ?? null,
    provenance: ["apigw_finalize"],
  });
  res.json({ ok: true, final: true, event: ev });
});

// Read model / projection (toy projection rebuilt on demand)
app.get("/state/:playerId", (req, res) => {
  const playerId = req.params.playerId;
  let lines = [];
  try { lines = fs.readFileSync(EVENT_SPINE, "utf-8").trim().split("\n").filter(Boolean); } catch {}
  const events = lines.map((l) => JSON.parse(l)).filter((e) => e.playerId === playerId || e.authoritativeState?.playerId === playerId);
  const lastFinal = [...events].reverse().find((e) => e.type === "finalization" && e.authoritativeState);
  const view = lastFinal?.authoritativeState ?? { playerId, x: 0, y: 0, hp: 100 };

  res.json({
    ok: true,
    playerId,
    state: view,
    provenance: lastFinal ? ["projection_from_event_spine", lastFinal.event_id] : ["projection_default"],
    pending: !lastFinal,
  });
});

// Debug: tail the last N events
app.get("/events/tail/:n", (req, res) => {
  const n = Math.max(1, Math.min(2000, parseInt(req.params.n, 10) || 50));
  let lines = [];
  try { lines = fs.readFileSync(EVENT_SPINE, "utf-8").trim().split("\n").filter(Boolean); } catch {}
  const tail = lines.slice(-n).map((l) => JSON.parse(l));
  res.json({ ok: true, n, events: tail });
});

app.listen(8000, () => console.log("API GW on :8000 (pending/final + event spine)"));

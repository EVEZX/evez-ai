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

function clamp01(value) {
  return Math.max(0, Math.min(1, Number(value) || 0));
}

class QuantumEmotionCore {
  constructor() {
    this.state = {
      curiosity: 0.55,
      urgency: 0.35,
      satisfaction: 0.4,
      frustration: 0.1,
      flow: 0.2,
    };
    this.meta = {
      dominantEmotion: "curiosity",
      taskThroughputMultiplier: 1,
      explorationRate: 1,
      selfMutationTriggered: false,
      lastUpdateTs: nowIso(),
      lastSignal: "boot",
    };
  }

  applySignals(signal = {}) {
    const progress = clamp01(signal.progress ?? signal.progressDelta ?? 0);
    const reward = clamp01(signal.reward ?? signal.rewardScore ?? 0);
    const blockage = clamp01(signal.blockage ?? signal.errorRate ?? 0);
    const novelty = clamp01(signal.novelty ?? signal.explorationSignal ?? 0);
    const throughput = clamp01(signal.throughput ?? signal.executionVelocity ?? 0);

    const next = {
      curiosity: clamp01(this.state.curiosity * 0.7 + novelty * 0.3 + (1 - progress) * 0.08),
      urgency: clamp01(this.state.urgency * 0.65 + (1 - progress) * 0.25 + blockage * 0.1),
      satisfaction: clamp01(this.state.satisfaction * 0.6 + progress * 0.25 + reward * 0.15),
      frustration: clamp01(this.state.frustration * 0.55 + blockage * 0.3 + (1 - reward) * 0.15),
      flow: clamp01(this.state.flow * 0.45 + progress * 0.25 + reward * 0.2 + throughput * 0.1 - blockage * 0.2),
    };

    this.state = next;
    const dominantEmotion = Object.entries(next).sort((a, b) => b[1] - a[1])[0][0];
    const isCurious = next.curiosity >= 0.72;
    const isFrustrated = next.frustration >= 0.68;
    const isFlowing = next.flow >= 0.7;

    this.meta = {
      dominantEmotion,
      explorationRate: isCurious ? 1.35 : 1,
      taskThroughputMultiplier: isFlowing ? 1.4 : 1,
      selfMutationTriggered: isFrustrated,
      lastUpdateTs: nowIso(),
      lastSignal: signal.source || "runtime",
    };

    return this.snapshot();
  }

  snapshot() {
    return {
      valence: { ...this.state },
      behavior: {
        explorationRate: this.meta.explorationRate,
        taskThroughputMultiplier: this.meta.taskThroughputMultiplier,
        selfMutationTriggered: this.meta.selfMutationTriggered,
      },
      dominantEmotion: this.meta.dominantEmotion,
      ts: this.meta.lastUpdateTs,
      lastSignal: this.meta.lastSignal,
    };
  }
}

const emotionCore = new QuantumEmotionCore();

// Pending vs Final guardrail: any non-authoritative state MUST be labeled.
app.get("/healthz", (_req, res) => res.json({ ok: true, ts: nowIso() }));

// Submit player input (always PENDING until game-server confirms)
app.post("/input", (req, res) => {
  const { playerId, input, progressSignals } = req.body || {};
  if (!playerId || !input) return res.status(400).json({ ok: false, error: "playerId + input required" });

  const emotion = emotionCore.applySignals({
    source: "input",
    ...(progressSignals || {}),
  });

  const ev = appendEvent({
    event_id: id("INPUT"),
    type: "player_input",
    ts: nowIso(),
    playerId,
    input,
    status: "pending",
    emotion,
    provenance: ["apigw"],
  });

  res.json({ ok: true, pending: true, event: ev });
});

// Mark an input as FINAL (normally done by authoritative game-server / reconciler)
app.post("/finalize/:eventId", (req, res) => {
  const { eventId } = req.params;
  const { authoritativeState, note, rewardLoop } = req.body || {};
  const emotion = emotionCore.applySignals({
    source: "reward_loop",
    progress: rewardLoop?.progress,
    reward: rewardLoop?.reward,
    blockage: rewardLoop?.blockage,
    novelty: rewardLoop?.novelty,
    throughput: rewardLoop?.throughput,
  });
  const ev = appendEvent({
    event_id: id("FINAL"),
    type: "finalization",
    ts: nowIso(),
    ref_event_id: eventId,
    status: "final",
    authoritativeState: authoritativeState ?? null,
    note: note ?? null,
    rewardLoop: rewardLoop ?? null,
    emotion,
    provenance: ["apigw_finalize"],
  });
  res.json({ ok: true, final: true, event: ev });
});

// Consciousness API: expose EvezBrain emotional valence + behavior modulation.
app.get("/consciousness", (_req, res) => {
  res.json({
    ok: true,
    module: "EvezBrain.quantum_emotion_core",
    emotion: emotionCore.snapshot(),
  });
});

// Optional external signal bridge for non-game task progress + reward loops.
app.post("/consciousness/signal", (req, res) => {
  const emotion = emotionCore.applySignals(req.body || {});
  const ev = appendEvent({
    event_id: id("EMOTE"),
    type: "emotion_update",
    ts: nowIso(),
    signal: req.body || {},
    emotion,
    provenance: ["apigw_consciousness"],
  });
  res.json({ ok: true, emotion, event: ev });
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

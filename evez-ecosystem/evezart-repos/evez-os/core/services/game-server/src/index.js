import { WebSocketServer } from "ws";
import fs from "fs";
import path from "path";
import crypto from "crypto";

const wss = new WebSocketServer({ port: 9001 });
console.log("Game Server WS on :9001");

const EVENT_SPINE = process.env.EVENT_SPINE || path.resolve("../..", "spine", "EVENT_SPINE.jsonl");
function nowIso() { return new Date().toISOString(); }
function id(prefix="EV") { return `${prefix}-${crypto.randomUUID()}`; }
function appendEvent(ev) {
  fs.mkdirSync(path.dirname(EVENT_SPINE), { recursive: true });
  fs.appendFileSync(EVENT_SPINE, JSON.stringify(ev) + "\n", "utf-8");
  return ev;
}

/**
 * Authoritative deterministic toy sim:
 * - state per player: {x,y,hp,seq}
 * - input: {dx,dy,seq}
 * - every tick applies queued inputs in order of seq
 */
const state = new Map(); // playerId -> {x,y,hp,seq}
const inputQ = new Map(); // playerId -> [{dx,dy,seq,receivedTs}]
let tick = 0;

function getState(pid){
  if(!state.has(pid)) state.set(pid, { playerId: pid, x:0, y:0, hp:100, seq:0 });
  if(!inputQ.has(pid)) inputQ.set(pid, []);
  return state.get(pid);
}

const TICK_HZ = Number(process.env.GAME_TICK_HZ || 60);
const TICK_MS = Math.floor(1000 / TICK_HZ);
const SNAPSHOT_HZ = Number(process.env.SNAPSHOT_HZ || 20);
const SNAPSHOT_EVERY = Math.max(1, Math.round(TICK_HZ / SNAPSHOT_HZ));
const MAX_REWIND_MS = Number(process.env.MAX_REWIND_MS || 250);


setInterval(() => {
  tick++;
  for (const [pid, q] of inputQ.entries()) {
    q.sort((a,b)=>a.seq-b.seq);
    const s = getState(pid);
    while(q.length && q[0].seq === s.seq + 1){
      const inp=q.shift();
      s.x += Math.max(-1, Math.min(1, inp.dx||0));
      s.y += Math.max(-1, Math.min(1, inp.dy||0));
      s.seq = inp.seq;
      appendEvent({
        event_id: id("AUTH"),
        type: "authoritative_step",
        ts: nowIso(),
        playerId: pid,
        applied_input: inp,
        authoritativeState: { ...s },
        provenance: ["game-server"],
      });
    }
  }
}, TICK_MS);

wss.on("connection", (ws) => {
  ws.send(JSON.stringify({ ok: true, authoritative: true, tickMs: TICK_MS }));

  ws.on("message", (buf) => {
    let msg;
    try { msg = JSON.parse(buf.toString("utf-8")); } catch { return; }
    const { playerId, input } = msg || {};
    if (!playerId || !input) {
      ws.send(JSON.stringify({ ok:false, error:"playerId+input required" }));
      return;
    }
    const s = getState(playerId);
    const seq = Number(input.seq || 0);
    if (!Number.isFinite(seq) || seq <= s.seq) {
      ws.send(JSON.stringify({ ok:false, error:"stale_seq", authoritativeSeq: s.seq }));
      return;
    }
    inputQ.get(playerId).push({ dx: input.dx||0, dy: input.dy||0, seq, receivedTs: nowIso() });

    // Immediate ack (pending). Client can do prediction locally.
    ws.send(JSON.stringify({ ok:true, pending:true, acceptedSeq: seq }));

    // Reconciliation packet (authoritative snapshot) after small delay
    setTimeout(() => {
      ws.send(JSON.stringify({ ok:true, authoritative:true, state: getState(playerId) }));
    }, 120);
  });
});

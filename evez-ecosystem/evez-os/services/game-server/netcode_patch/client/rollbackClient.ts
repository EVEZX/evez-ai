// client/rollbackClient.ts (reference implementation)
// Runs in browser or node. Keeps input & state history and performs rollback on snapshot divergence.

import type { ClientMsg, ServerMsg, InputCmd, Snapshot, State } from "../shared/protocol";

type PredictedFrame = { tick: number; state: State };

export type RollbackClientOptions = {
  tickRate?: number;
  maxRewindMs?: number;
  inputBufferMs?: number;
};

export class RollbackClient {
  ws: WebSocket;
  playerId: string = "";
  tickRate = 60;
  serverTick = 0;

  // buffers
  seq = 0;
  inputHistory: InputCmd[] = [];
  stateHistory: PredictedFrame[] = [];

  // current predicted state
  state: State = { tick: 0, playerId: "", x: 0, y: 0, vx: 0, vy: 0 };

  // config
  maxHistory = 120;          // ~6s at 20Hz
  epsPos = 0.02;             // divergence threshold
  epsVel = 0.05;

  constructor(url: string) {
    this.ws = new WebSocket(url);
    this.ws.onmessage = (ev) => this.onServer(JSON.parse(ev.data) as ServerMsg);
  }

  send(msg: ClientMsg) {
    this.ws.send(JSON.stringify(msg));
  }

  onServer(msg: ServerMsg) {
    if (msg.type === "hello") {
      this.tickRate = msg.tickRate;
      this.serverTick = msg.serverTick;
      // @ts-ignore demo includes playerId
      this.playerId = msg.playerId;
      this.state.playerId = this.playerId;
      return;
    }

    if (msg.type === "snapshot") {
      this.onSnapshot(msg.snap);
    }
  }

  // deterministic local sim must match server applyInput
  applyInputLocal(s: State, cmd: InputCmd) {
    const DT = 1 / this.tickRate;
    const ax = cmd.moveX * 20;
    const ay = cmd.moveY * 20;
    s.vx += ax * DT;
    s.vy += ay * DT;
    s.x += s.vx * DT;
    s.y += s.vy * DT;
  }

  pushHistory() {
    this.stateHistory.push({ tick: this.state.tick, state: { ...this.state } });
    if (this.stateHistory.length > this.maxHistory) this.stateHistory.shift();
  }

  // called by your render loop
  step(moveX: number, moveY: number, buttons: number, dtMs: number) {
    if (!this.playerId) return;

    // advance predicted tick
    this.state.tick += 1;

    // build cmd
    const cmd: InputCmd = {
      playerId: this.playerId,
      seq: ++this.seq,
      tick: this.state.tick,
      dtMs,
      moveX,
      moveY,
      buttons,
    };

    // record + send
    this.inputHistory.push(cmd);
    if (this.inputHistory.length > this.maxHistory) this.inputHistory.shift();
    this.send({ type: "input", cmd });

    // predict locally
    this.applyInputLocal(this.state, cmd);

    // store predicted frame
    this.pushHistory();
  }

  findPredictedAtTick(tick: number): PredictedFrame | undefined {
    return this.stateHistory.find(f => f.tick === tick);
  }

  onSnapshot(snap: Snapshot) {
    if (snap.state.playerId !== this.playerId) return;

    // 1) compare to predicted state at snap.tick
    const predicted = this.findPredictedAtTick(snap.tick);
    const shouldRollback = !predicted || this.diverged(predicted.state, snap.state);

    if (!shouldRollback) {
      // prune acknowledged inputs
      this.inputHistory = this.inputHistory.filter(i => i.seq > snap.lastProcessedSeq);
      return;
    }

    // 2) rollback: set state to authoritative snapshot
    this.state = { ...snap.state };

    // 3) re-simulate inputs after lastProcessedSeq in order
    const replay = this.inputHistory.filter(i => i.seq > snap.lastProcessedSeq).sort((a,b)=>a.seq-b.seq);

    // rebuild history from snap.tick forward
    this.stateHistory = this.stateHistory.filter(f => f.tick < snap.tick);
    for (const cmd of replay) {
      // advance tick deterministically
      this.state.tick += 1;
      this.applyInputLocal(this.state, cmd);
      this.pushHistory();
    }
  }

  diverged(a: State, b: State): boolean {
    const dx = Math.abs(a.x - b.x);
    const dy = Math.abs(a.y - b.y);
    const dvx = Math.abs(a.vx - b.vx);
    const dvy = Math.abs(a.vy - b.vy);
    return (dx > this.epsPos) || (dy > this.epsPos) || (dvx > this.epsVel) || (dvy > this.epsVel);
  }
}

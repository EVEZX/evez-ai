// shared/protocol.ts
export type Tick = number;
export type PlayerId = string;

export type InputCmd = {
  playerId: PlayerId;
  seq: number;          // strictly increasing per player
  tick: Tick;           // client-predicted tick when input was generated
  dtMs: number;         // client frame delta (for diagnostics)
  moveX: number;        // -1..1
  moveY: number;        // -1..1
  buttons: number;      // bitmask
};

export type State = {
  tick: Tick;
  playerId: PlayerId;
  x: number;
  y: number;
  vx: number;
  vy: number;
};

export type Snapshot = {
  tick: Tick;                 // authoritative tick of this state
  lastProcessedSeq: number;   // last input seq applied for this player
  state: State;
  // hash is optional but recommended; use a stable hash of quantized state
  hash?: number;
};

export type ServerMsg =
  | { type: "hello"; serverTick: Tick; tickRate: number }
  | { type: "snapshot"; snap: Snapshot }
  | { type: "pong"; tClient: number; tServer: number };

export type ClientMsg =
  | { type: "input"; cmd: InputCmd }
  | { type: "ping"; tClient: number };

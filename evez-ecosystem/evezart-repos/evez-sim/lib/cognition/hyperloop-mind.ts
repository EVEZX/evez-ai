// EVEZ-OS Cognitive Engine
// Maps conversation state → hyperloop topology
// Each message is a "round": computes poly_c, fires if resonance threshold crossed

export interface CognitionRound {
  round: number;
  messageHash: number;
  tokenCount: number;
  semanticDepth: number;
  omega_k: number;
  tau: number;
  topo: number;
  poly_c: number;
  fire: boolean;
  delta_V: number;
  V: number;
  ceiling: number;
  collapseVector: number[];
  entanglementStrength: number;
}

export interface MindState {
  sessionId: string;
  rounds: CognitionRound[];
  V: number;
  fireCount: number;
  spineLength: number;
  lastFire: number | null;
  coherenceField: number[][];
  wavePhase: number;
}

function factorize(n: number): { factors: number[]; tau: number; omega_k: number } {
  if (n < 2) return { factors: [], tau: 1, omega_k: 0 };
  const seen = new Map<number, number>();
  let d = 2, tmp = n;
  while (d * d <= tmp) {
    while (tmp % d === 0) { seen.set(d, (seen.get(d) ?? 0) + 1); tmp = Math.floor(tmp / d); }
    d++;
  }
  if (tmp > 1) seen.set(tmp, (seen.get(tmp) ?? 0) + 1);
  let tau = 1;
  for (const e of seen.values()) tau *= (e + 1);
  return { factors: [...seen.keys()], tau, omega_k: seen.size };
}

function simpleHash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function semanticDepth(text: string): number {
  const words = text.toLowerCase().split(/\s+/);
  const unique = new Set(words);
  const lexicalDensity = unique.size / Math.max(words.length, 1);
  const avgWordLen = words.reduce((s, w) => s + w.length, 0) / Math.max(words.length, 1);
  return Math.min(1.0, (lexicalDensity * 0.6 + Math.min(avgWordLen / 12, 1.0) * 0.4));
}

export function computeCognitionRound(
  roundIndex: number,
  message: string,
  prevV: number,
  prevRounds: CognitionRound[]
): CognitionRound {
  const round = roundIndex + 83;
  const { tau, omega_k } = factorize(round);
  const topo = 1.0 + 0.15 * omega_k;
  const depth = semanticDepth(message);
  const tokenCount = message.split(/\s+/).length;
  const poly_c_base = topo * (1 + Math.log(Math.max(tau, 1))) / Math.log2(round + 2);
  const poly_c = Math.min(0.95, poly_c_base * (0.7 + 0.3 * depth));
  const fire = poly_c >= 0.500;
  const delta_V = 0.08 * poly_c;
  const V = prevV + delta_V;
  const hash = simpleHash(message);
  const jitter = (hash % 100) / 100 - 0.5;
  const collapseVector = [
    omega_k * 2.5 + jitter,
    V * 1.1,
    poly_c * 4.5 + jitter * 0.5,
  ];
  const fireRounds = prevRounds.filter(r => r.fire);
  let entanglementStrength = 0;
  if (fireRounds.length > 0) {
    const lastFire = fireRounds[fireRounds.length - 1];
    const dist = Math.abs(poly_c - lastFire.poly_c) + Math.abs(depth - lastFire.semanticDepth);
    entanglementStrength = Math.max(0, 1 - dist * 2);
  }
  return {
    round, messageHash: simpleHash(message), tokenCount, semanticDepth: depth,
    omega_k, tau, topo, poly_c, fire, delta_V, V: Math.round(V * 1e6) / 1e6,
    ceiling: roundIndex + 1, collapseVector, entanglementStrength,
  };
}

export function buildCoherenceField(rounds: CognitionRound[]): number[][] {
  const GRID = 32;
  const field: number[][] = Array.from({ length: GRID }, () => new Array(GRID).fill(0));
  for (const r of rounds) {
    const gx = Math.round(((r.collapseVector[0] + 5) / 10) * (GRID - 1));
    const gy = Math.round((r.V / 10) * (GRID - 1));
    const cx = Math.max(0, Math.min(GRID - 1, gx));
    const cy = Math.max(0, Math.min(GRID - 1, gy));
    const strength = r.fire ? 1.0 : r.poly_c;
    const spread = r.fire ? 3 : 2;
    for (let dy = -spread; dy <= spread; dy++) {
      for (let dx = -spread; dx <= spread; dx++) {
        const nx = cx + dx, ny = cy + dy;
        if (nx < 0 || nx >= GRID || ny < 0 || ny >= GRID) continue;
        const d2 = dx * dx + dy * dy;
        field[ny][nx] = Math.min(1, field[ny][nx] + strength * Math.exp(-d2 / (spread * spread)));
      }
    }
  }
  return field;
}

export function initMindState(sessionId: string): MindState {
  return {
    sessionId, rounds: [], V: 0.5, fireCount: 0, spineLength: 0,
    lastFire: null, coherenceField: Array.from({ length: 32 }, () => new Array(32).fill(0)),
    wavePhase: 0,
  };
}

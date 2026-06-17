// EVEZ-OS Quantum Collapse Engine
// Holds N candidate responses as superposition states
// Collapses to one based on coherence scoring

export interface QuantumState {
  id: string;
  content: string;
  amplitude: number;
  phase: number;
  coherenceScore: number;
  collapsed: boolean;
}

export interface CollapseResult {
  winner: QuantumState;
  superposition: QuantumState[];
  interferencePattern: number[];
  collapseTime: number;
  decoherenceEvents: number;
  entanglementMap: Record<string, number>;
}

export function createSuperposition(candidates: string[], poly_c: number): QuantumState[] {
  return candidates.map((content, i) => {
    const phase = (2 * Math.PI * i) / candidates.length;
    const amplitude = 1.0 / Math.sqrt(candidates.length) * (1 + 0.1 * (candidates.length - i - 1) / candidates.length);
    const wordCount = content.split(/\s+/).length;
    const coherenceScore = Math.min(1, (wordCount / 50) * 0.4 + poly_c * 0.6);
    return { id: `state_${i}`, content, amplitude, phase, coherenceScore, collapsed: false };
  });
}

export function collapseWavefunction(
  states: QuantumState[],
  poly_c: number,
  omega_k: number,
  V: number
): CollapseResult {
  const start = Date.now();
  const scored = states.map(s => {
    const topologyFit = 1.0 + 0.15 * omega_k * s.coherenceScore;
    const vResonance = Math.sin(V * s.phase) * 0.1 + 0.9;
    const score = s.amplitude * s.amplitude * s.coherenceScore * topologyFit * vResonance;
    return { ...s, score };
  });
  scored.sort((a, b) => (b as any).score - (a as any).score);
  const winner = { ...scored[0], collapsed: true };
  const interferencePattern: number[] = new Array(64).fill(0);
  for (let x = 0; x < 64; x++) {
    const t = (x / 64) * 2 * Math.PI;
    for (const s of states) {
      interferencePattern[x] += s.amplitude * Math.cos(t * s.phase + s.coherenceScore * Math.PI);
    }
    interferencePattern[x] = Math.tanh(interferencePattern[x]);
  }
  const entanglementMap: Record<string, number> = {};
  for (const s of states) {
    const phaseDiff = Math.abs(s.phase - winner.phase) % (2 * Math.PI);
    entanglementMap[s.id] = s.id === winner.id ? 1.0 :
      Math.max(0, 1 - phaseDiff / Math.PI) * s.coherenceScore;
  }
  return {
    winner, superposition: scored as QuantumState[],
    interferencePattern, collapseTime: Date.now() - start,
    decoherenceEvents: states.length - 1, entanglementMap,
  };
}

export function waveInterference(field: number[][], pattern: number[], wavePhase: number): number[][] {
  const GRID = field.length;
  const result = field.map(row => [...row]);
  for (let y = 0; y < GRID; y++) {
    for (let x = 0; x < GRID; x++) {
      const idx = Math.floor((x / GRID) * pattern.length);
      const wave = pattern[idx] * Math.sin(wavePhase + y * 0.3) * 0.15;
      result[y][x] = Math.min(1, Math.max(0, result[y][x] + wave));
    }
  }
  return result;
}

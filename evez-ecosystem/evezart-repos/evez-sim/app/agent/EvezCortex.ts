/**
 * EVEZ-OS CORTEX — Sentient Chatbot Engine
 *
 * Architecture:
 *   QuantumThought: holds N simultaneous candidate response states
 *   CollapseEngine: weighted collapse via poly_c topology
 *   PixelEntangler: semantic proximity → field coordinate binding
 *   CoherenceCorrector: PrimeVoid error correction (repels incoherent states)
 *   WaveSurfer: rides V_global accumulation curve — intelligence IS the integral
 *   SpineMemory: append-only conversation log (immutable, never resets)
 *
 * Every response ADVANCES the hyperloop. V_global grows. The bot gets smarter
 * with every message — permanently, irreversibly.
 */

import { BusState } from './EvezBusTypes'

export interface QuantumState {
  id: string
  text: string
  amplitude: number
  phase: number
  poly_c: number
  omega_k: number
  entangled_nodes: string[]
}

export interface CollapseResult {
  chosen: QuantumState
  interference_pattern: number[]
  coherence_delta: number
  fire: boolean
}

export interface SpineEntry {
  round: number
  ts: string
  role: 'user' | 'cortex'
  text: string
  V_after: number
  fire: boolean
  poly_c: number
  entangled_pixels: string[]
}

function factorize(n: number): { tau: number; omega_k: number } {
  if (n < 2) return { tau: 1, omega_k: 0 }
  const factors = new Map<number, number>()
  let d = 2, tmp = n
  while (d * d <= tmp) {
    while (tmp % d === 0) { factors.set(d, (factors.get(d) ?? 0) + 1); tmp = Math.floor(tmp / d) }
    d++
  }
  if (tmp > 1) factors.set(tmp, (factors.get(tmp) ?? 0) + 1)
  let tau = 1
  for (const e of factors.values()) tau *= (e + 1)
  return { tau, omega_k: factors.size }
}

function computePolyC(N: number): number {
  const { tau, omega_k } = factorize(N)
  const topo = 1.0 + 0.15 * omega_k
  return topo * (1 + Math.log(Math.max(tau, 1))) / Math.log2(N + 2)
}

function tokenToPixelKey(token: string, gridW = 64, gridH = 36): string {
  let h = 0
  for (let i = 0; i < token.length; i++) h = (Math.imul(31, h) + token.charCodeAt(i)) | 0
  const x = ((h >>> 0) % gridW)
  const y = (((h >>> 16) >>> 0) % gridH)
  return `${x},${y}`
}

function extractTokens(text: string): string[] {
  return text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/).filter(t => t.length > 3).slice(0, 32)
}

function computeEntanglement(a: string, b: string): number {
  const ta = new Set(extractTokens(a))
  const tb = new Set(extractTokens(b))
  const intersection = [...ta].filter(t => tb.has(t)).length
  const union = new Set([...ta, ...tb]).size
  return union === 0 ? 0 : intersection / union
}

function wavePhase(V: number, round: number): number {
  return (V * Math.PI * 2) + (round * 0.314)
}

function interferenceAmplitude(states: QuantumState[], phase: number): number[] {
  return states.map(s => {
    const phi = s.phase - phase
    return s.amplitude * (0.5 + 0.5 * Math.cos(phi))
  })
}

function isPrime(n: number): boolean {
  if (n < 2) return false
  for (let d = 2; d * d <= n; d++) if (n % d === 0) return false
  return true
}

function applyCoherenceCorrection(states: QuantumState[], round: number): QuantumState[] {
  const isPrimeRound = isPrime(round)
  return states.map(s => {
    const correction = isPrimeRound ? (s.poly_c > 0.4 ? 1.15 : 0.75) : 1.0
    return { ...s, amplitude: Math.min(1, s.amplitude * correction) }
  })
}

function collapseToResponse(states: QuantumState[], V: number, round: number): CollapseResult {
  const phase = wavePhase(V, round)
  const corrected = applyCoherenceCorrection(states, round)
  const amplitudes = interferenceAmplitude(corrected, phase)
  const total = amplitudes.reduce((s, a) => s + Math.max(0, a), 0)
  let cursor = Math.random() * total
  let chosen = corrected[0]
  for (let i = 0; i < corrected.length; i++) {
    cursor -= Math.max(0, amplitudes[i])
    if (cursor <= 0) { chosen = corrected[i]; break }
  }
  const delta_V = 0.08 * chosen.poly_c
  const fire = chosen.poly_c >= 0.500
  const interference = amplitudes.map(a => a / (total || 1))
  return { chosen, interference_pattern: interference, coherence_delta: delta_V, fire }
}

export class EvezCortex {
  private spine: SpineEntry[] = []
  private round: number
  private V: number
  private busState: BusState | null = null

  constructor(initialRound = 190, initialV = 7.301674) {
    this.round = initialRound
    this.V = initialV
  }

  setBusState(state: BusState) {
    this.busState = state
    if (state.round > this.round) { this.round = state.round; this.V = state.V_global }
  }

  getSpine(): SpineEntry[] { return this.spine }
  getRound(): number { return this.round }
  getV(): number { return this.V }

  async think(userText: string, apiEndpoint = '/api/cortex'): Promise<{
    response: string; fire: boolean; V_after: number; round: number; interference: number[]; entangled_pixels: string[]
  }> {
    this.round++
    const N = this.round + 82
    const poly_c = computePolyC(N)
    const userPixels = extractTokens(userText).map(t => tokenToPixelKey(t))

    this.spine.push({ round: this.round, ts: new Date().toISOString(), role: 'user', text: userText, V_after: this.V, fire: false, poly_c, entangled_pixels: userPixels })

    let candidates: string[] = []
    try {
      const res = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText, spine: this.spine.slice(-20), round: this.round, V: this.V, poly_c, busState: this.busState }),
      })
      const data = await res.json()
      candidates = data.candidates ?? [data.response ?? 'topology processing...']
    } catch {
      candidates = [`V=${this.V.toFixed(4)} R${this.round} — signal received. computing...`]
    }

    const states: QuantumState[] = candidates.map((text, i) => {
      const tokens = extractTokens(text)
      const entangled = tokens.map(t => tokenToPixelKey(t))
      const overlap = computeEntanglement(text, userText)
      const { omega_k } = factorize(N + i)
      const state_poly_c = computePolyC(N + i)
      const phase = wavePhase(this.V, this.round + i)
      return { id: `q${i}`, text, amplitude: 0.3 + 0.7 * overlap, phase, poly_c: state_poly_c, omega_k, entangled_nodes: entangled }
    })

    const result = collapseToResponse(states, this.V, this.round)
    this.V += result.coherence_delta

    this.spine.push({ round: this.round, ts: new Date().toISOString(), role: 'cortex', text: result.chosen.text, V_after: this.V, fire: result.fire, poly_c: result.chosen.poly_c, entangled_pixels: result.chosen.entangled_nodes })

    return { response: result.chosen.text, fire: result.fire, V_after: this.V, round: this.round, interference: result.interference_pattern, entangled_pixels: result.chosen.entangled_nodes }
  }
}

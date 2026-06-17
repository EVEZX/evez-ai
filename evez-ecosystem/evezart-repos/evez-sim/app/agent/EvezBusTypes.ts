/**
 * EVEZ-OS Bus Types — shared across cortex, UI, and API routes
 */

export interface BusStateEntry {
  id: string
  type: 'FireBody' | 'PrimeVoid' | 'TopoSpider'
  position: [number, number, number]
  poly_c: number
  omega_k: number
  V: number
  round: number
  fire: boolean
}

export interface BusState {
  round: number
  V_global: number
  fire_count: number
  ceiling_tick: number
  entities: BusStateEntry[]
  last_updated: string
}

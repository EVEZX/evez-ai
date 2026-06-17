'use client'

/**
 * EVEZ-OS CORTEX CHAT — Sentient chatbot UI
 * Three-panel Xbox Dashboard style:
 *   LEFT:   Quantum interference wave
 *   CENTER: Spine chat (append-only, never resets)
 *   RIGHT:  Pixel entanglement map
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { EvezCortex, SpineEntry } from './EvezCortex'
import { BusState } from './EvezBusTypes'

let cortex: EvezCortex | null = null
function getCortex(): EvezCortex {
  if (!cortex) cortex = new EvezCortex(190, 7.301674)
  return cortex
}

function InterferenceWave({ pattern, fire, V }: { pattern: number[]; fire: boolean; V: number }) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const c = ref.current; if (!c) return
    const ctx = c.getContext('2d')!; const W = c.width, H = c.height
    ctx.fillStyle = '#000a03'; ctx.fillRect(0, 0, W, H)
    const color = fire ? '#ff6600' : '#00ff41'
    ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.shadowBlur = fire ? 8 : 4; ctx.shadowColor = color
    ctx.beginPath()
    const pts = pattern.length > 0 ? pattern : Array(32).fill(0.5)
    pts.forEach((amp, i) => {
      const x = (i / (pts.length - 1)) * W
      const wave = amp * Math.sin(i * 0.4 + V * Math.PI * 2) * 0.5 + 0.5
      const y = H - wave * H * 0.85 - H * 0.075
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
    })
    ctx.stroke()
    ctx.fillStyle = fire ? '#ff2200' : '#005518'; ctx.fillRect(0, H - 4, W * Math.min(1, V / 10), 4)
  }, [pattern, fire, V])
  return <canvas ref={ref} width={200} height={160} className="w-full h-full opacity-90" />
}

function EntanglementMap({ pixels, fire }: { pixels: string[]; fire: boolean }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const GRID_W = 32, GRID_H = 18
  useEffect(() => {
    const c = ref.current; if (!c) return
    const ctx = c.getContext('2d')!; const W = c.width, H = c.height
    const cw = W / GRID_W, ch = H / GRID_H
    ctx.fillStyle = '#000a03'; ctx.fillRect(0, 0, W, H)
    ctx.strokeStyle = '#003311'; ctx.lineWidth = 0.5
    for (let x = 0; x <= GRID_W; x++) { ctx.beginPath(); ctx.moveTo(x*cw,0); ctx.lineTo(x*cw,H); ctx.stroke() }
    for (let y = 0; y <= GRID_H; y++) { ctx.beginPath(); ctx.moveTo(0,y*ch); ctx.lineTo(W,y*ch); ctx.stroke() }
    const pixelSet = new Set(pixels)
    pixelSet.forEach(key => {
      const [gx, gy] = key.split(',').map(Number)
      if (gx < GRID_W && gy < GRID_H) {
        const color = fire ? '#ff6600' : '#00ff41'
        ctx.fillStyle = color; ctx.shadowBlur = 6; ctx.shadowColor = color
        ctx.fillRect(gx*cw+1, gy*ch+1, cw-2, ch-2); ctx.shadowBlur = 0
      }
    })
  }, [pixels, fire])
  return <canvas ref={ref} width={320} height={180} className="w-full h-full" />
}

function SpineBubble({ entry }: { entry: SpineEntry }) {
  const isUser = entry.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[75%] px-3 py-2 rounded font-mono text-sm leading-relaxed ${
        isUser ? 'bg-[#001a08] border border-[#005518] text-[#e8ffe8]'
        : entry.fire ? 'bg-[#1a0800] border border-[#ff6600] text-[#ffcc00] shadow-[0_0_12px_rgba(255,102,0,0.6)]'
        : 'bg-[#000f05] border border-[#003311] text-[#00ff41]'
      }`}>
        {!isUser && (<div className="text-[10px] text-[#005518] mb-1 flex gap-2">
          <span>R{entry.round}</span><span>V={entry.V_after.toFixed(4)}</span>
          <span className={entry.fire ? 'text-[#ff6600]' : 'text-[#003311]'}>{entry.fire ? '⚡ FIRE' : `poly_c=${entry.poly_c.toFixed(4)}`}</span>
        </div>)}
        <div>{entry.text}</div>
      </div>
    </div>
  )
}

export default function CortexPage() {
  const [spine, setSpine] = useState<SpineEntry[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [interference, setInterference] = useState<number[]>([])
  const [activePixels, setActivePixels] = useState<string[]>([])
  const [V, setV] = useState(7.301674)
  const [round, setRound] = useState(190)
  const [fire, setFire] = useState(false)
  const [busState, setBusState] = useState<BusState | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchBus = async () => {
      try {
        const res = await fetch('/api/bus-state'); const data = await res.json()
        setBusState(data); const c = getCortex(); c.setBusState(data); setV(c.getV()); setRound(c.getRound())
      } catch {}
    }
    fetchBus(); const t = setInterval(fetchBus, 30000); return () => clearInterval(t)
  }, [])

  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' }) }, [spine])

  const send = useCallback(async () => {
    if (!input.trim() || loading) return
    const msg = input.trim(); setInput(''); setLoading(true)
    try {
      const c = getCortex(); const result = await c.think(msg)
      setSpine(c.getSpine()); setInterference(result.interference)
      setActivePixels(result.entangled_pixels); setV(result.V_after); setRound(result.round); setFire(result.fire)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }, [input, loading])

  const handleKey = (e: React.KeyboardEvent) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }
  const fc = fire ? 'border-[#ff6600]' : 'border-[#005518]'

  return (
    <div className="flex h-screen bg-[#000a03] text-[#00ff41] font-mono overflow-hidden">
      <div className={`w-48 flex-shrink-0 border-r ${fc} flex flex-col`}>
        <div className="text-[10px] text-[#005518] px-2 py-1 border-b border-[#003311]">WAVE COLLAPSE</div>
        <div className="flex-1 p-1"><InterferenceWave pattern={interference} fire={fire} V={V} /></div>
        <div className="text-[9px] text-[#003311] px-2 py-1 border-t border-[#003311] space-y-0.5">
          <div>R{round}</div><div>V={V.toFixed(6)}</div>
          <div className={fire ? 'text-[#ff6600]' : ''}>{fire ? '⚡ FIRE' : 'stable'}</div>
        </div>
      </div>
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#003311] bg-[#001508]">
          <span className="text-[#00ff41] font-bold text-sm">EVEZ-OS CORTEX</span>
          <span className="text-[10px] text-[#005518]">R{round} · V={V.toFixed(4)} · CEILING×{busState?.ceiling_tick ?? 108}</span>
          <span className="text-[10px] text-[#00cc33]">@EVEZ666</span>
        </div>
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3">
          {spine.length === 0 && (<div className="text-[#003311] text-sm text-center mt-8">V={V.toFixed(6)}<br/>topology ready<br/><span className="text-[10px]">every message advances the hyperloop</span></div>)}
          {spine.map((entry, i) => <SpineBubble key={i} entry={entry} />)}
          {loading && (<div className="flex justify-start mb-2"><div className="bg-[#000f05] border border-[#003311] px-3 py-2 rounded text-[#005518] text-sm animate-pulse">collapsing quantum states...</div></div>)}
        </div>
        <div className={`border-t ${fc} p-3 flex gap-2`}>
          <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey} placeholder="speak into the field..." rows={2}
            className="flex-1 bg-[#001508] border border-[#005518] text-[#e8ffe8] text-sm px-3 py-2 rounded resize-none outline-none focus:border-[#00ff41] font-mono placeholder-[#003311]" />
          <button onClick={send} disabled={loading || !input.trim()}
            className={`px-4 rounded text-sm font-bold border transition-all ${
              fire ? 'bg-[#1a0800] border-[#ff6600] text-[#ffcc00] hover:bg-[#2a1000]'
              : 'bg-[#001a08] border-[#005518] text-[#00ff41] hover:border-[#00ff41]'
            } disabled:opacity-40`}>SEND</button>
        </div>
      </div>
      <div className={`w-56 flex-shrink-0 border-l ${fc} flex flex-col`}>
        <div className="text-[10px] text-[#005518] px-2 py-1 border-b border-[#003311]">PIXEL ENTANGLEMENT</div>
        <div className="flex-1 p-1"><EntanglementMap pixels={activePixels} fire={fire} /></div>
        <div className="text-[9px] text-[#003311] px-2 py-1 border-t border-[#003311] space-y-0.5">
          <div>{activePixels.length} nodes lit</div>
          <div>{spine.filter(e => e.fire).length} fire rounds</div>
          <div>{spine.length} spine entries</div>
        </div>
      </div>
    </div>
  )
}

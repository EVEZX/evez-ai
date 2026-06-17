'use client'
import React, { useState, useRef } from 'react'

// EVEZ-OS FSC ENGINE game loop
// Failure-Surface Cartography as playable level structure
// Full source with EventSpine + BIAS CONSTITUTION in packages/evez-sim-core

type DiagnoseLayer = 'client'|'cdn'|'dns'|'bgp'|'auth'|'origin'|'ws'|'game_server'|'matchmaking'|'spine'
type Phase = 'idle'|'probing'|'diagnosed'|'evaluated'

const LAYER_LABELS: Record<DiagnoseLayer,string> = {
  client:'Client / Renderer', cdn:'Edge / CDN', dns:'DNS / Resolvers', bgp:'BGP / Routing',
  auth:'Auth / Identity', origin:'Origin / API GW', ws:'WebSocket Gateway',
  game_server:'Authoritative Game Server', matchmaking:'Matchmaking / Econ', spine:'EVENT SPINE'
}
const ALL_LAYERS = Object.keys(LAYER_LABELS) as DiagnoseLayer[]

const SYMPTOMS: Record<string,string> = {
  synchrony_assumption: 'Event A appears before Event B but A depends on B. Clock skew?',
  first_signal_canon: 'First response says 200 OK but subsequent probes show 404. Which is real?',
  speed_equals_truth: 'CDN cache returns stale data at 8ms. Origin returns correct data at 340ms.',
  single_villain_model: 'Auth failure, BGP flap, and cert expiry all coincide. Which is causal?',
  narrative_completion: 'Sequence looks complete: req\u2192resp\u2192ack. But ack is from cache, not origin.',
  confidence_theater: 'Agent reports 98% confidence on a diagnosis with only one vantage point.',
}

const VANTAGE: Record<DiagnoseLayer,string> = {
  cdn: 'Origin returns V=7.240012. CDN returns V=7.194717. Delta=45ms stale. TTL not invalidated post-R188.',
  dns: 'Google resolver: 104.21.x.x (correct). ISP resolver: NXDOMAIN. Split-horizon confirmed.',
  bgp: 'US-West: 3 hops, 14ms. EU-Central: 18 hops via AS6453 transit leak. Route exists. Path is wrong.',
  auth: 'Server Date vs Client clock: delta=194s. JWT exp=5min. Clock skew consumed the token.',
  origin: 'Direct: 200 OK 8ms. Via proxy: 502. Origin healthy. Gateway rate-limit on proxy egress IP.',
  client: 'Client: 05:14:47. NTP: 05:14:58. 11s drift. Prediction engine over-compensating.',
  ws: 'WiFi: stays open. Cellular: drops at 32s. Carrier idle-timeout=30s. Heartbeat=60s. Interval too long.',
  game_server: 'Replica A: hit tick 4421. Replica B: miss tick 4421. Read replica lag 340ms.',
  matchmaking: 'Skill gap expanding 0.3\u03c3/week. Fill speed metric is misaligned incentive.',
  spine: 'Node 1&2: sha256=a3f... Node 3: sha256=b9c... Silent edit detected. Spine integrity violation.',
}

export default function FSCGameLoop() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [probe, setProbe] = useState<{layer:DiagnoseLayer;symptom:string;mode:string}|null>(null)
  const [vantage, setVantage] = useState<string|null>(null)
  const [playerLayer, setPlayerLayer] = useState<DiagnoseLayer|null>(null)
  const [score, setScore] = useState({omega:0,sigma:0})
  const [V, setV] = useState(0.5)
  const [history, setHistory] = useState<boolean[]>([])
  const [result, setResult] = useState<{correct:boolean;msg:string}|null>(null)
  const modes = Object.keys(SYMPTOMS)

  function nextProbe() {
    const layer = ALL_LAYERS[Math.floor(Math.random()*ALL_LAYERS.length)]
    const mode = modes[Math.floor(Math.random()*modes.length)]
    setProbe({layer,symptom:SYMPTOMS[mode],mode})
    setVantage(null); setPlayerLayer(null); setResult(null); setPhase('probing')
  }

  function commit() {
    if (!probe||!playerLayer) return
    const correct = playerLayer===probe.layer && vantage!==null
    const dV = correct ? (vantage ? 0.08 : 0.04) : 0
    const msg = correct
      ? `\u03a9 UPGRADE \u2014 survived ${probe.mode} on ${probe.layer}${vantage?' (vantage bonus)':''}`
      : `\u03a3f EXTRACTED \u2014 diagnosed ${playerLayer} instead of ${probe.layer}${!vantage?' + no second vantage':''}`
    setScore(s => ({omega:s.omega+(correct?1:0), sigma:s.sigma+(correct?0:1)}))
    setV(v => v+dV)
    setHistory(h => [...h,correct].slice(-10))
    setResult({correct,msg}); setPhase('evaluated')
  }

  const btn = (bg:string,text:string,border?:string) => ({
    background:bg, color:text, border:`1px solid ${border??bg}`,
    borderRadius:4, padding:'8px 14px', cursor:'pointer',
    fontFamily:'monospace', fontSize:11, fontWeight:'bold' as const, textAlign:'left' as const
  })

  return (
    <div style={{background:'#000a03',color:'#e8ffe8',fontFamily:'monospace',minHeight:'100vh',display:'flex',flexDirection:'column'}}>
      <div style={{background:'rgba(0,21,8,0.95)',borderBottom:'1px solid #003311',padding:'8px 16px',display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:8}}>
        <span style={{color:'#00ff41',fontWeight:'bold'}}>FSC ENGINE</span>
        <span style={{fontSize:11,color:'#00cc33'}}>Ω={score.omega} &nbsp;·&nbsp; Σf={score.sigma} &nbsp;·&nbsp; V={V.toFixed(4)} &nbsp;·&nbsp; spine={score.omega+score.sigma}</span>
        <span style={{fontSize:10,color:'#003311'}}>@EVEZ666 · prove it.</span>
      </div>
      <div style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',padding:'24px 16px',gap:20,maxWidth:700,margin:'0 auto',width:'100%'}}>
        {phase==='idle'&&(
          <div style={{textAlign:'center',gap:16,display:'flex',flexDirection:'column',alignItems:'center'}}>
            <div style={{fontSize:13,color:'#00cc33',lineHeight:1.8}}>The FSC ENGINE injects a controlled failure at one layer.<br/>Your job: isolate the layer. Use a second vantage. Prove it.<br/><span style={{color:'#003311'}}>Confidence without evidence is a tax you pay in public.</span></div>
            <button onClick={nextProbe} style={btn('#00ff41','#000a03')}>START PROBE</button>
          </div>
        )}
        {(phase==='probing'||phase==='diagnosed')&&probe&&(
          <div style={{width:'100%',display:'flex',flexDirection:'column',gap:14}}>
            <div style={{background:'#001a08',border:'1px solid #003311',borderRadius:6,padding:'12px 16px'}}>
              <div style={{color:'#003311',fontSize:10,marginBottom:4}}>OBSERVED SYMPTOM</div>
              <div style={{color:'#e8ffe8',fontSize:13,lineHeight:1.7}}>{probe.symptom}</div>
              <div style={{color:'#003311',fontSize:10,marginTop:6}}>truth_state: <span style={{color:'#00ff41'}}>pending</span></div>
            </div>
            {!vantage&&<button onClick={()=>setVantage(VANTAGE[probe.layer])} style={btn('#005518','#00ff41')}>PROBE SECOND VANTAGE</button>}
            {vantage&&<div style={{background:'#000f05',border:'1px solid #005518',borderRadius:6,padding:'10px 14px',fontSize:11}}><div style={{color:'#005518',marginBottom:4}}>VANTAGE RESULT</div><div style={{color:'#00cc33'}}>{vantage}</div></div>}
            {phase==='probing'&&<>
              <div style={{color:'#003311',fontSize:10}}>SELECT RESPONSIBLE LAYER:</div>
              <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(180px,1fr))',gap:6}}>
                {ALL_LAYERS.map(l=>(<button key={l} onClick={()=>{setPlayerLayer(l);setPhase('diagnosed')}} style={btn('#001a08','#00cc33','#003311')}>{LAYER_LABELS[l]}</button>))}
              </div>
            </>}
            {phase==='diagnosed'&&(
              <div style={{display:'flex',flexDirection:'column',gap:8}}>
                <div style={{color:'#ff6600',fontSize:11}}>Diagnosed: <strong>{playerLayer&&LAYER_LABELS[playerLayer]}</strong> &nbsp; Vantage: <strong style={{color:vantage?'#00ff41':'#ff2200'}}>{vantage?'YES':'NO — are you sure?'}</strong></div>
                {!vantage&&<button onClick={()=>setVantage(VANTAGE[probe.layer])} style={btn('#1a0800','#ff6600')}>GET SECOND VANTAGE FIRST</button>}
                <button onClick={commit} style={btn(vantage?'#00ff41':'#ff6600','#000a03')}>COMMIT DIAGNOSIS → prove it</button>
              </div>
            )}
          </div>
        )}
        {phase==='evaluated'&&result&&(
          <div style={{width:'100%',display:'flex',flexDirection:'column',gap:14}}>
            <div style={{background:result.correct?'rgba(0,255,65,0.05)':'rgba(255,34,0,0.06)',border:`1px solid ${result.correct?'#00ff41':'#ff2200'}`,borderRadius:6,padding:'14px 16px'}}>
              <div style={{color:result.correct?'#00ff41':'#ff2200',fontWeight:'bold',marginBottom:6}}>{result.correct?'\u03a9 UPGRADE \u2014 SURVIVED':'\u03a3f EXTRACTED \u2014 COLLAPSE'}</div>
              <div style={{color:'#e8ffe8',fontSize:12,lineHeight:1.7}}>{result.msg}</div>
              {!result.correct&&<div style={{color:'#003311',fontSize:10,marginTop:8}}>This collapse is in the EVENT SPINE. It cannot be removed. Learn from it.</div>}
            </div>
            <div style={{display:'flex',gap:4,flexWrap:'wrap'}}>{history.map((h,i)=>(<div key={i} style={{width:12,height:12,borderRadius:2,background:h?'#00ff41':'#ff2200'}}/>))}</div>
            <button onClick={nextProbe} style={btn('#00ff41','#000a03')}>NEXT PROBE</button>
          </div>
        )}
      </div>
    </div>
  )
}
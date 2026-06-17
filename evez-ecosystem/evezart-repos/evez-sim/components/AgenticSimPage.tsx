'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import * as THREE from 'three'

const P = { bg:0x000a03, green:0x00ff41, green2:0x00cc33, green3:0x005518, fire:0xff6600, fire2:0xff2200, white:0xe8ffe8, dim:0x003311, cyan:0x00ffff, yellow:0xffaa00, red:0xff2200 }

function buildMesh(c: any, scene: THREE.Scene): THREE.Object3D {
  let m: THREE.Object3D
  if (c.type==='fire_body') {
    const r=(c.poly_c??0.55)*2.0; const g=new THREE.Group()
    g.add(new THREE.Mesh(new THREE.SphereGeometry(r*0.5,14,10),new THREE.MeshBasicMaterial({color:P.fire})))
    g.add(new THREE.Mesh(new THREE.SphereGeometry(r*1.7,10,8),new THREE.MeshBasicMaterial({color:P.fire,transparent:true,opacity:0.07,side:THREE.BackSide})))
    m=g
  } else if (c.type==='prime_void') {
    const r=Math.log2(c.N??89)*0.6; const g=new THREE.Group()
    g.add(new THREE.Mesh(new THREE.TorusGeometry(r*0.5,r*0.07,8,24),new THREE.MeshBasicMaterial({color:P.dim,transparent:true,opacity:0.5})))
    g.add(new THREE.Mesh(new THREE.TorusGeometry(r*0.9,r*0.03,6,18),new THREE.MeshBasicMaterial({color:P.red,transparent:true,opacity:0.15})))
    m=g
  } else {
    const r=0.45; const g=new THREE.Group()
    g.add(new THREE.Mesh(new THREE.BoxGeometry(r,r,r),new THREE.MeshBasicMaterial({color:P.green2,wireframe:true,transparent:true,opacity:0.3})))
    g.add(new THREE.Mesh(new THREE.SphereGeometry(r*0.15,6,4),new THREE.MeshBasicMaterial({color:P.cyan})))
    m=g
  }
  scene.add(m); return m
}

function placeCircuit(c: any, idx: number, total: number): [number,number,number] {
  const angle=(idx/total)*Math.PI*2
  if(c.type==='fire_body')   return [Math.cos(angle)*(3+idx*0.9), 2+Math.sin(angle*3)*3, Math.sin(angle)*(3+idx*0.9)]
  if(c.type==='prime_void')  return [Math.cos(angle)*(13+(c.N??89)*0.05), -3+Math.cos(angle*2)*2, Math.sin(angle)*(13+(c.N??89)*0.05)]
  return [Math.cos(angle)*(8+idx*0.5), 5+Math.cos(angle)*2, Math.sin(angle)*(8+idx*0.5)]
}

// ── Payment Gate ─────────────────────────────────────────────────────────────
function PaymentGate({ onEnter }: { onEnter: () => void }) {
  const [loading, setLoading] = useState(false)
  const [demo, setDemo] = useState(false)
  
  useEffect(() => {
    // Check if Stripe is configured
    fetch('/api/checkout').then(r => r.json()).then((d: any) => {
      if (!d.configured) setDemo(true)
    }).catch(() => setDemo(true))
  }, [])

  const handlePay = async () => {
    setLoading(true)
    try {
      const r = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin: window.location.origin })
      })
      const d = await r.json() as { url?: string; demo?: boolean }
      if (d.demo || !d.url) { onEnter(); return }
      window.location.href = d.url
    } catch { setLoading(false) }
  }

  const s = {
    overlay: { position:'fixed' as const, inset:0, background:'rgba(0,10,3,0.97)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:100, fontFamily:'monospace' },
    box: { border:'1px solid #003311', padding:'32px 40px', maxWidth:400, textAlign:'center' as const },
    title: { color:'#00ff41', fontSize:18, fontWeight:'bold', marginBottom:8 },
    sub: { color:'#e8ffe8', fontSize:11, marginBottom:4, lineHeight:1.6 },
    dim: { color:'#003311', fontSize:10, marginBottom:24 },
    btn: { background:'#00ff41', color:'#000a03', border:'none', padding:'12px 32px', fontSize:13, fontWeight:'bold', cursor:'pointer', fontFamily:'monospace', width:'100%', marginBottom:8 },
    skip: { color:'#003311', fontSize:10, cursor:'pointer', textDecoration:'underline' as const, background:'none', border:'none', fontFamily:'monospace' }
  }

  return (
    <div style={s.overlay}>
      <div style={s.box}>
        <div style={s.title}>EVEZ-OS AGENT FIELD</div>
        <div style={s.sub}>Live circuit physics. These are real AI processes.</div>
        <div style={s.sub}>FireBody = active circuit. PrimeVoid = blocker. TopoSpider = probe.</div>
        <div style={s.dim}>Updates every 30s from the hyperloop.</div>
        {demo ? (
          <button style={s.btn} onClick={onEnter}>ENTER (DEMO MODE)</button>
        ) : (
          <button style={s.btn} onClick={handlePay} disabled={loading}>
            {loading ? 'REDIRECTING...' : 'ENTER — $5 ONE TIME'}
          </button>
        )}
        <div/>
        <button style={s.skip} onClick={onEnter}>skip for now →</button>
      </div>
    </div>
  )
}

export default function AgenticSimPage() {
  const mountRef=useRef<HTMLDivElement>(null)
  const stateRef=useRef<any>(null)
  const frameRef=useRef(0)
  const [busState,setBusState]=useState<any>(null)
  const [mobile,setMobile]=useState(false)
  const [gated,setGated]=useState(true)

  // Check URL param ?paid=1 (Stripe redirect back)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const p = new URLSearchParams(window.location.search)
      if (p.get('paid') === '1') setGated(false)
    }
  }, [])

  const fetchBus=useCallback(async()=>{
    try{const r=await fetch('/api/bus-state');const d=await r.json();stateRef.current=d;setBusState(d)}catch{}
  },[])

  useEffect(()=>{if(!gated){fetchBus();const iv=setInterval(fetchBus,30000);return()=>clearInterval(iv)}},[fetchBus,gated])

  useEffect(()=>{
    if(gated) return
    const isMobile=window.innerWidth<768; setMobile(isMobile)
    const el=mountRef.current!
    if(!el) return
    const scene=new THREE.Scene(); scene.background=new THREE.Color(P.bg); scene.fog=new THREE.FogExp2(P.bg,0.011)
    const camera=new THREE.PerspectiveCamera(isMobile?70:58,el.clientWidth/el.clientHeight,0.1,400)
    camera.position.set(22,14,32); camera.lookAt(0,2,0)
    const renderer=new THREE.WebGLRenderer({antialias:!isMobile,powerPreference:'low-power'})
    renderer.setSize(el.clientWidth,el.clientHeight); renderer.setPixelRatio(Math.min(window.devicePixelRatio,isMobile?1.5:2))
    el.appendChild(renderer.domElement)
    scene.add(new THREE.AmbientLight(0x00ff41,0.2))
    const firePt=new THREE.PointLight(P.fire,3,30); scene.add(firePt)
    const grid=new THREE.GridHelper(60,20,P.green3,P.dim); grid.position.y=-4;
    (grid.material as THREE.Material).transparent=true;(grid.material as THREE.Material).opacity=0.10; scene.add(grid)

    let meshMap=new Map<string,THREE.Object3D>()
    let phases=new Map<string,number>()
    let circuits: any[]=[]

    function rebuild(entities: any[]){
      Array.from(meshMap.values()).forEach(m=>scene.remove(m))
      meshMap=new Map(); phases=new Map(); circuits=entities
      entities.forEach((c,i)=>{
        const m=buildMesh(c,scene); const pos=placeCircuit(c,i,entities.length)
        m.position.set(...pos); meshMap.set(c.id,m); phases.set(c.id,Math.random()*Math.PI*2)
      })
    }

    const initIv=setInterval(()=>{ if(stateRef.current){clearInterval(initIv);rebuild(stateRef.current.entities)} },100)
    const linePts=new Float32Array(600); const lineGeo=new THREE.BufferGeometry()
    lineGeo.setAttribute('position',new THREE.BufferAttribute(linePts,3))
    scene.add(new THREE.LineSegments(lineGeo,new THREE.LineBasicMaterial({color:P.green3,transparent:true,opacity:0.12})))
    let camTheta=0,lastRebuild=0

    function animate(){
      frameRef.current=requestAnimationFrame(animate); const dt=1/60; const now=Date.now()
      if(stateRef.current&&now-lastRebuild>30000){rebuild(stateRef.current.entities);lastRebuild=now}
      const fc=new THREE.Vector3(0,2,0); let fcount=0
      circuits.forEach(c=>{
        const m=meshMap.get(c.id); if(!m)return
        const ph=(phases.get(c.id)??0)+dt*(c.type==='fire_body'?0.8:c.type==='topo_spider'?1.2:0.15); phases.set(c.id,ph)
        const pulse=0.5+0.5*Math.sin(ph)
        if(c.type==='fire_body'){m.scale.setScalar(0.92+0.08*pulse);fc.add(m.position);fcount++;m.rotation.y+=dt*0.3}
        else if(c.type==='topo_spider'){m.rotation.y+=dt*0.9;m.rotation.x+=dt*0.3;m.position.x+=(fc.x/Math.max(fcount,1)-m.position.x)*dt*0.08;m.position.z+=(fc.z/Math.max(fcount,1)-m.position.z)*dt*0.08}
        else{m.rotation.z+=dt*0.06;const ch=(m as THREE.Group).children;if(ch[1])ch[1].scale.setScalar(1+0.15*pulse)}
      })
      if(fcount>0){fc.divideScalar(fcount);firePt.position.copy(fc)}
      let ptr=0,ec=0
      for(let i=0;i<circuits.length&&ec<100;i++)for(let j=i+1;j<circuits.length&&ec<100;j++){
        const mi=meshMap.get(circuits[i].id),mj=meshMap.get(circuits[j].id); if(!mi||!mj)continue
        if(mi.position.distanceTo(mj.position)<14&&circuits[i].type!=='prime_void'&&circuits[j].type!=='prime_void'){
          linePts[ptr++]=mi.position.x;linePts[ptr++]=mi.position.y;linePts[ptr++]=mi.position.z
          linePts[ptr++]=mj.position.x;linePts[ptr++]=mj.position.y;linePts[ptr++]=mj.position.z;ec++
        }
      }
      lineGeo.attributes.position.needsUpdate=true; lineGeo.setDrawRange(0,ec*2)
      camTheta+=dt*0.003; const R=isMobile?36:46
      camera.position.x=Math.cos(camTheta)*R; camera.position.z=Math.sin(camTheta)*R; camera.position.y=14+4*Math.sin(camTheta*0.2)
      camera.lookAt(0,2,0); renderer.render(scene,camera)
    }
    animate()
    const onResize=()=>{camera.aspect=el.clientWidth/el.clientHeight;camera.updateProjectionMatrix();renderer.setSize(el.clientWidth,el.clientHeight)}
    window.addEventListener('resize',onResize)
    return()=>{ clearInterval(initIv); cancelAnimationFrame(frameRef.current); window.removeEventListener('resize',onResize); renderer.dispose(); if(el.contains(renderer.domElement))el.removeChild(renderer.domElement) }
  },[gated])

  const hc: Record<string,string>={'GREEN':'#00ff41','YELLOW':'#ffaa00','RED':'#ff2200'}
  return (
    <div style={{position:'relative',width:'100%',height:'100dvh',background:'#000a03',overflow:'hidden'}}>
      {gated && <PaymentGate onEnter={()=>setGated(false)} />}
      <div ref={mountRef} style={{width:'100%',height:'100%'}} />
      {!gated && (
        <>
          <div style={{position:'absolute',top:0,left:0,right:0,background:'rgba(0,10,3,0.92)',borderBottom:'1px solid #003311',padding:'6px 14px',display:'flex',justifyContent:'space-between',alignItems:'center',fontFamily:'monospace',zIndex:20,flexWrap:'wrap' as const,gap:4}}>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <span style={{color:'#00ff41',fontWeight:'bold',fontSize:12}}>EVEZ-OS</span>
              <span style={{color:'#003311',fontSize:10}}>agentic operating surface</span>
            </div>
            <div style={{display:'flex',gap:10,fontSize:10,color:'#e8ffe8',alignItems:'center'}}>
              <span style={{color:hc[busState?.circuit_health??'GREEN']}}>{busState?.circuit_health??'…'}</span>
              <span>R{busState?.current_round??189}</span>
              <span>V={busState?.V_global?.toFixed(4)??'7.2400'}</span>
              <span style={{color:'#ff6600'}}>{busState?.fires??7} fire</span>
              <span style={{color:'#ff2200'}}>{busState?.voids??4} void</span>
              <span style={{color:'#00ffff'}}>{busState?.spiders??3} probe</span>
            </div>
            <span style={{color:'#003311',fontSize:9}}>@EVEZ666</span>
          </div>
          <div style={{position:'absolute',...(mobile?{bottom:0,left:0,right:0,borderTop:'1px solid #003311' as const}:{bottom:20,left:12,border:'1px solid #003311',borderRadius:4,width:240}),background:'rgba(0,10,3,0.90)',padding:'7px 12px',fontFamily:'monospace',fontSize:9,zIndex:20}}>
            <div style={{display:'flex',gap:mobile?14:0,flexDirection:mobile?'row' as const:'column' as const,flexWrap:'wrap' as const,justifyContent:mobile?'center' as const:'flex-start' as const}}>
              {[{color:'#ff6600',label:`FireBody ×${busState?.fires??7} — active circuits`},{color:'#ff2200',label:`PrimeVoid ×${busState?.voids??4} — blockers`},{color:'#00ffff',label:`TopoSpider ×${busState?.spiders??3} — probes`}].map(({color,label})=>(
                <div key={label} style={{display:'flex',alignItems:'center',gap:5,marginBottom:mobile?0:3}}>
                  <div style={{width:7,height:7,borderRadius:'50%',background:color,flexShrink:0}} />
                  <span style={{color:'#e8ffe8'}}>{label}</span>
                </div>
              ))}
            </div>
            {!mobile&&<div style={{marginTop:5,color:'#003311',borderTop:'1px solid #001a08',paddingTop:4}}>30s live · /api/bus-state · spine append-only</div>}
          </div>
        </>
      )}
    </div>
  )
}
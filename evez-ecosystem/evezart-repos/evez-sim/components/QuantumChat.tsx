'use client';
import React, { useState, useRef, useEffect, useCallback } from 'react';

interface CognitionMeta {
  round: number; poly_c: number; fire: boolean; V: number; delta_V: number;
  omega_k: number; tau: number; entanglementStrength: number; collapseVector: number[];
}
interface Message {
  role: 'user' | 'assistant'; content: string;
  cognition?: CognitionMeta;
  collapse?: { decoherenceEvents: number; collapseTime: number; interferencePattern: number[]; superpositionCount: number; };
  timestamp: number;
}
interface Props {
  onFieldUpdate?: (field: number[][], wavePhase: number, cognition: CognitionMeta) => void;
  className?: string;
  style?: React.CSSProperties;
}

const G='#00ff41',G2='#00cc33',G3='#005518',F='#ff6600',F2='#ff2200',C='#00ccff',GOLD='#ffcc00',V0='#000a03',DIM='#003311',W='#e8ffe8';

export function QuantumChat({ onFieldUpdate, className='', style }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mindState, setMindState] = useState({ V: 7.259260, fireCount: 35, rounds: [] as any[] });
  const [currentCollapse, setCurrentCollapse] = useState<number[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas||!currentCollapse.length) return;
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    const W2=canvas.width,H=canvas.height;
    ctx.fillStyle=V0; ctx.fillRect(0,0,W2,H);
    const grad=ctx.createLinearGradient(0,0,W2,0);
    grad.addColorStop(0,C+'88'); grad.addColorStop(0.5,G+'cc'); grad.addColorStop(1,F+'88');
    ctx.strokeStyle=grad; ctx.lineWidth=1.5; ctx.beginPath();
    for(let x=0;x<W2;x++){const idx=Math.floor((x/W2)*currentCollapse.length);const y=H/2+currentCollapse[idx]*(H/2-4);if(x===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}
    ctx.stroke();
    ctx.fillStyle=G+'08'; for(let y=0;y<H;y+=3){ctx.fillRect(0,y,W2,1);}
  },[currentCollapse]);

  useEffect(()=>{endRef.current?.scrollIntoView({behavior:'smooth'});},[messages]);

  const send = useCallback(async()=>{
    if(!input.trim()||loading) return;
    const userMsg:Message={role:'user',content:input.trim(),timestamp:Date.now()};
    setMessages(p=>[...p,userMsg]); setInput(''); setLoading(true);
    try {
      const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({message:userMsg.content,history:messages.slice(-8).map(m=>({role:m.role,content:m.content})),mindState})});
      const data=await res.json();
      setMessages(p=>[...p,{role:'assistant',content:data.response,cognition:data.cognition,collapse:data.collapse,timestamp:Date.now()}]);
      if(data.collapse?.interferencePattern) setCurrentCollapse(data.collapse.interferencePattern);
      setMindState(p=>({V:data.cognition?.V??p.V,fireCount:p.fireCount+(data.cognition?.fire?1:0),rounds:[...p.rounds,data.cognition].filter(Boolean)}));
      if(onFieldUpdate&&data.field) onFieldUpdate(data.field.coherenceField,data.field.wavePhase,data.cognition);
    } catch {
      setMessages(p=>[...p,{role:'assistant',content:'DECOHERENCE EVENT — signal lost',timestamp:Date.now()}]);
    } finally { setLoading(false); }
  },[input,loading,messages,mindState,onFieldUpdate]);

  return (
    <div className={`flex flex-col ${className}`} style={{background:V0,border:`1px solid ${G3}`,fontFamily:'monospace',fontSize:13,color:G,position:'relative',...style}}>
      <div style={{padding:'6px 10px',borderBottom:`1px solid ${G3}`,display:'flex',justifyContent:'space-between',fontSize:11}}>
        <span style={{color:G,fontWeight:'bold'}}>EVEZ-OS MIND</span>
        <span style={{color:C}}>V={mindState.V.toFixed(6)}</span>
        <span style={{color:F}}>FIRE×{mindState.fireCount}</span>
        <span style={{color:G2}}>R×{mindState.rounds.length}</span>
      </div>
      <canvas ref={canvasRef} width={400} height={28} style={{width:'100%',height:28,display:'block',opacity:currentCollapse.length?1:0.2}}/>
      <div style={{flex:1,overflowY:'auto',padding:'8px 10px',minHeight:200,maxHeight:320}}>
        {messages.length===0&&<div style={{color:DIM,fontSize:11,textAlign:'center',marginTop:40}}>V=7.259260 · 35 fires · 189 rounds<br/><span style={{color:G3}}>mind is listening</span></div>}
        {messages.map((msg,i)=>(
          <div key={i} style={{marginBottom:10}}>
            <div style={{fontSize:10,color:msg.role==='user'?C:(msg.cognition?.fire?F:G2),marginBottom:2}}>
              {msg.role==='user'?'▸ INPUT':`▸ EVEZ-OS${msg.cognition?` · poly_c=${msg.cognition.poly_c.toFixed(4)} · ${msg.cognition.fire?'🔥 FIRE':'stable'} · ω_k=${msg.cognition.omega_k}`:''}`}
            </div>
            <div style={{color:msg.role==='user'?W:(msg.cognition?.fire?'#ffcc88':G),lineHeight:1.5,whiteSpace:'pre-wrap',wordBreak:'break-word',borderLeft:`2px solid ${msg.cognition?.fire?F:(msg.role==='user'?C:G3)}`,paddingLeft:8}}>
              {msg.content}
            </div>
            {msg.collapse&&<div style={{fontSize:9,color:DIM,marginTop:3}}>collapse {msg.collapse.collapseTime}ms · {msg.collapse.decoherenceEvents} decoherence · entangle={msg.cognition?.entanglementStrength.toFixed(3)}</div>}
          </div>
        ))}
        {loading&&<div style={{color:C,fontSize:11}}>▸ EVEZ-OS <span style={{color:G3}}>· superposition active · collapsing ◈◈◈</span></div>}
        <div ref={endRef}/>
      </div>
      <div style={{display:'flex',borderTop:`1px solid ${G3}`,padding:'6px 8px',gap:6,alignItems:'flex-end'}}>
        <textarea value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}}} placeholder="inject signal..." rows={2}
          style={{flex:1,background:'transparent',border:`1px solid ${G3}`,color:G,fontFamily:'monospace',fontSize:12,padding:'4px 6px',resize:'none',outline:'none',borderRadius:2}}/>
        <button onClick={send} disabled={loading||!input.trim()} style={{background:loading?G3:G,color:V0,border:'none',fontFamily:'monospace',fontWeight:'bold',fontSize:11,padding:'6px 10px',cursor:loading?'default':'pointer',borderRadius:2,alignSelf:'stretch'}}>
          {loading?'◈◈':'FIRE'}
        </button>
      </div>
    </div>
  );
}

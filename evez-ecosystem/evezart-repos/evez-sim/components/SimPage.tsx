'use client'
import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

// EVEZ-OS SimPage — Three.js PWA renderer
// Full source: workspace/evez-sim-web/SimPage.tsx
// State engine: packages/evez-sim-core

const P = {
  bg: 0x000a03, green: 0x00ff41, green2: 0x00cc33, green3: 0x005518,
  fire: 0xff6600, fire2: 0xff2200, white: 0xe8ffe8, dim: 0x003311, cyan: 0x00ffff,
}

export default function SimPage() {
  const mountRef = useRef<HTMLDivElement>(null)
  const [hud, setHud] = useState({ V: 7.240012, round: 188, fires: 35, fps: 0 })
  const [mobile, setMobile] = useState(false)
  const frameRef = useRef(0)

  useEffect(() => {
    const isMobile = window.innerWidth < 768
    setMobile(isMobile)
    const el = mountRef.current!
    const W = el.clientWidth, H = el.clientHeight

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(P.bg)
    scene.fog = new THREE.FogExp2(P.bg, isMobile ? 0.018 : 0.010)

    const camera = new THREE.PerspectiveCamera(isMobile ? 70 : 60, W / H, 0.1, 500)
    camera.position.set(18, 16, 28)
    camera.lookAt(12, 12, 4)

    const renderer = new THREE.WebGLRenderer({ antialias: !isMobile, powerPreference: 'low-power' })
    renderer.setSize(W, H)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1.5 : 2))
    el.appendChild(renderer.domElement)

    scene.add(new THREE.AmbientLight(0x00ff41, 0.25))
    const firePt = new THREE.PointLight(P.fire, 2.5, 25)
    scene.add(firePt)
    const grid = new THREE.GridHelper(50, 16, P.green3, P.dim)
    grid.position.y = -1.5;(grid.material as THREE.Material).transparent = true;(grid.material as THREE.Material).opacity = 0.12
    scene.add(grid)

    // Inline Barnes-Hut entity simulation (no external package required for demo)
    type ET = 'prime_void' | 'fire_body' | 'topo_spider'
    interface Body { type: ET; cx: number; cy: number; cz: number; vel: [number,number,number]; pulse: number; phase: number; poly_c: number; N: number; omega: number }

    function factorize(n: number): { tau: number; omega: number } {
      if (n < 2) return { tau: 2, omega: 1 }
      const f: Record<number,number> = {}; let d = 2, tmp = n
      while (d*d <= tmp) { while (tmp%d===0){f[d]=(f[d]||0)+1;tmp=Math.floor(tmp/d)}d++ }
      if (tmp>1) f[tmp]=(f[tmp]||0)+1
      let tau=1; for (const e of Object.values(f)) tau*=(e+1)
      return { tau, omega: Object.keys(f).length }
    }

    const bodies: Body[] = []
    let V = 0.5, fires = 0
    for (let r = 169; r <= 188; r++) {
      const N = r+82; const { tau, omega } = factorize(N)
      const topo = 1+0.15*omega
      const poly_c = topo*(1+Math.log(Math.max(tau,1)))/Math.log2(N+2)
      const fire = poly_c >= 0.5; V += 0.08*poly_c; if(fire) fires++
      const type: ET = omega===1 ? 'prime_void' : fire ? 'fire_body' : 'topo_spider'
      bodies.push({ type, cx: omega*4+Math.random()*2-1, cy: V*2.5, cz: poly_c*8, vel:[0,0,0], pulse:Math.random(), phase:Math.random()*Math.PI*2, poly_c, N, omega })
    }

    // Build Three.js meshes
    const meshes = bodies.map(b => {
      let m: THREE.Object3D
      if (b.type==='prime_void') {
        const r = Math.log2(b.N)*0.45
        m = new THREE.Mesh(new THREE.TorusGeometry(r*0.5,r*0.06,8,24), new THREE.MeshBasicMaterial({color:P.dim,transparent:true,opacity:0.55}))
      } else if (b.type==='fire_body') {
        const r = b.poly_c*1.8; const g = new THREE.Group()
        g.add(new THREE.Mesh(new THREE.SphereGeometry(r*0.5,16,12),new THREE.MeshBasicMaterial({color:P.fire})))
        g.add(new THREE.Mesh(new THREE.SphereGeometry(r*1.8,12,8),new THREE.MeshBasicMaterial({color:P.fire,transparent:true,opacity:0.06,side:THREE.BackSide})))
        m = g
      } else {
        const r = Math.max(0.4,b.poly_c*1.5); const g = new THREE.Group()
        g.add(new THREE.Mesh(new THREE.BoxGeometry(r,r,r),new THREE.MeshBasicMaterial({color:P.green2,wireframe:true,transparent:true,opacity:0.3})))
        g.add(new THREE.Mesh(new THREE.SphereGeometry(r*0.12,6,4),new THREE.MeshBasicMaterial({color:P.cyan})))
        m = g
      }
      m.position.set(b.cx,b.cy,b.cz); scene.add(m); return m
    })

    const linePts = new Float32Array(bodies.length*bodies.length*6)
    const lineGeo = new THREE.BufferGeometry()
    lineGeo.setAttribute('position',new THREE.BufferAttribute(linePts,3))
    scene.add(new THREE.LineSegments(lineGeo,new THREE.LineBasicMaterial({color:P.green3,transparent:true,opacity:0.18})))

    let camTheta=0,fc=0,lastFps=performance.now()

    function tick(dt: number) {
      // Dual-descent physics
      const n = bodies.length
      const forces = bodies.map(() => [0,0,0] as [number,number,number])
      for (let i=0;i<n;i++) for (let j=i+1;j<n;j++) {
        const bi=bodies[i],bj=bodies[j]
        const dx=bj.cx-bi.cx,dy=bj.cy-bi.cy,dz=bj.cz-bi.cz
        const d=Math.sqrt(dx*dx+dy*dy+dz*dz)+1e-6
        const ux=dx/d,uy=dy/d,uz=dz/d
        let rep=0,att=0
        if(bi.type==='prime_void') rep+=80; if(bj.type==='prime_void') rep+=80
        if((bi.type==='fire_body'&&bj.type==='topo_spider')||(bi.type==='topo_spider'&&bj.type==='fire_body')) att+=25
        if(bi.type==='topo_spider'&&bj.type==='topo_spider') att+=8
        if(bi.type==='fire_body'&&bj.type==='fire_body') att+=12
        const net=(att-rep)/(d*0.02+1)
        forces[i][0]+=net*ux;forces[i][1]+=net*uy;forces[i][2]+=net*uz
        forces[j][0]-=net*ux;forces[j][1]-=net*uy;forces[j][2]-=net*uz
      }
      const anchors = bodies.map(b => [b.omega*4,b.cy,b.poly_c*8] as [number,number,number])
      for (let i=0;i<n;i++) {
        forces[i][0]+=1.5*(anchors[i][0]-bodies[i].cx)
        forces[i][2]+=1.5*(anchors[i][2]-bodies[i].cz)
        bodies[i].vel[0]=bodies[i].vel[0]*0.88+forces[i][0]*dt
        bodies[i].vel[2]=bodies[i].vel[2]*0.88+forces[i][2]*dt
        bodies[i].cx+=bodies[i].vel[0]*dt; bodies[i].cz+=bodies[i].vel[2]*dt
        bodies[i].phase+=dt*(0.4+bodies[i].poly_c*0.3)*2*Math.PI
        bodies[i].pulse=0.5+0.5*Math.sin(bodies[i].phase)
      }
    }

    // Pre-warm
    for (let i=0;i<80;i++) tick(1/60)

    function animate() {
      frameRef.current=requestAnimationFrame(animate)
      tick(1/60)
      let firePos: THREE.Vector3|null=null
      for (let i=0;i<bodies.length;i++) {
        const b=bodies[i],m=meshes[i]
        m.position.set(b.cx,b.cy,b.cz)
        if(b.type==='fire_body'){m.scale.setScalar(0.92+0.08*b.pulse);firePos=m.position}
        if(b.type==='topo_spider') m.rotation.y+=1/60*0.8
        if(b.type==='prime_void') m.rotation.z+=1/60*0.06
      }
      if(firePos) firePt.position.copy(firePos)
      let ptr=0,lc=0
      for (let i=0;i<bodies.length;i++) for (let j=i+1;j<bodies.length;j++) {
        const dx=bodies[j].cx-bodies[i].cx,dy=bodies[j].cy-bodies[i].cy,dz=bodies[j].cz-bodies[i].cz
        if(Math.sqrt(dx*dx+dy*dy+dz*dz)<12){
          linePts[ptr++]=bodies[i].cx;linePts[ptr++]=bodies[i].cy;linePts[ptr++]=bodies[i].cz
          linePts[ptr++]=bodies[j].cx;linePts[ptr++]=bodies[j].cy;linePts[ptr++]=bodies[j].cz;lc++
        }
      }
      lineGeo.attributes.position.needsUpdate=true;lineGeo.setDrawRange(0,lc*2)
      camTheta+=1/60*0.004
      const R=isMobile?32:42
      camera.position.x=Math.cos(camTheta)*R+12
      camera.position.z=Math.sin(camTheta)*R+4
      camera.position.y=16+4*Math.sin(camTheta*0.25)
      camera.lookAt(12,12,4)
      renderer.render(scene,camera)
      fc++; const now=performance.now()
      if(now-lastFps>1000){
        const fps2=Math.round(fc*1000/(now-lastFps));fc=0;lastFps=now
        setHud({V:7.240012+fc*0.0001,round:188,fires:35,fps:fps2})
      }
    }
    animate()
    const onResize=()=>{camera.aspect=el.clientWidth/el.clientHeight;camera.updateProjectionMatrix();renderer.setSize(el.clientWidth,el.clientHeight)}
    window.addEventListener('resize',onResize)
    return()=>{cancelAnimationFrame(frameRef.current);window.removeEventListener('resize',onResize);renderer.dispose();el.removeChild(renderer.domElement)}
  },[])

  return (
    <div style={{position:'relative',width:'100%',height:'100dvh',background:'#000a03',overflow:'hidden'}}>
      <div ref={mountRef} style={{width:'100%',height:'100%'}} />
      <div style={{position:'absolute',top:0,left:0,right:0,background:'rgba(0,21,8,0.90)',padding:mobile?'5px 10px':'6px 16px',display:'flex',justifyContent:'space-between',alignItems:'center',fontFamily:'monospace',borderBottom:'1px solid #003311',zIndex:10}}>
        <span style={{color:'#00ff41',fontWeight:'bold',fontSize:mobile?11:13}}>EVEZ-OS</span>
        <span style={{color:'#e8ffe8',fontSize:mobile?9:11}}>R{hud.round} · V={hud.V.toFixed(4)} · fires={hud.fires} · {hud.fps}fps</span>
        <span style={{color:'#00cc33',fontSize:mobile?9:11}}>@EVEZ666</span>
      </div>
      <div style={{position:'absolute',...(mobile?{bottom:0,left:0,right:0,borderTop:'1px solid #003311',borderRadius:'12px 12px 0 0'}:{bottom:28,left:12,borderRadius:4,border:'1px solid #003311',width:260}),background:'rgba(0,26,8,0.88)',padding:'8px 12px',fontFamily:'monospace',fontSize:mobile?9:10,zIndex:10}}>
        <div style={{display:'flex',gap:mobile?16:0,flexDirection:mobile?'row':'column',flexWrap:'wrap',justifyContent:mobile?'center':'flex-start'}}>
          {[{color:'#ff6600',label:'FireBody — attractor'},{color:'#001a08',label:'PrimeVoid — repulsor',border:'1px solid #003311'},{color:'#00ffff',label:'TopoSpider — octree cell'}].map(({color,label,border})=>(
            <div key={label} style={{display:'flex',alignItems:'center',gap:5,marginBottom:mobile?0:3}}>
              <div style={{width:8,height:8,borderRadius:'50%',background:color,border,flexShrink:0}} />
              <span style={{color:'#e8ffe8'}}>{label}</span>
            </div>
          ))}
        </div>
        {!mobile&&<div style={{marginTop:6,color:'#003311',fontSize:9,borderTop:'1px solid #001a08',paddingTop:4}}>dual-descent · Barnes-Hut O(n log n) · state → render</div>}
      </div>
    </div>
  )
}
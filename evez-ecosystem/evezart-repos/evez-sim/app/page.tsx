import Link from 'next/link'

export default function Home() {
  return (
    <div style={{background:'#000a03',color:'#e8ffe8',fontFamily:'monospace',minHeight:'100vh',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:24,padding:24}}>
      <div style={{textAlign:'center'}}>
        <div style={{color:'#00ff41',fontSize:22,fontWeight:'bold',letterSpacing:2}}>EVEZ-OS</div>
        <div style={{color:'#003311',fontSize:11,marginTop:4}}>Barnes-Hut \u00b7 dual-descent \u00b7 FSC ENGINE \u00b7 agentic OS</div>
      </div>
      <div style={{display:'flex',flexDirection:'column',gap:12,width:'100%',maxWidth:340}}>
        <Link href="/agent" style={ls('#00ff41')}>
          \u2192 AGENT OS  <span style={{color:'#003311',fontSize:10}}>live circuit cockpit \u00b7 AI pilots</span>
        </Link>
        <Link href="/sim" style={ls('#00cc33')}>
          \u2192 SIMULATION  <span style={{color:'#003311',fontSize:10}}>Three.js \u00b7 octree \u00b7 60fps</span>
        </Link>
        <Link href="/fsc" style={ls('#ff6600')}>
          \u2192 FSC ENGINE  <span style={{color:'#003311',fontSize:10}}>failure cartography \u00b7 prove it</span>
        </Link>
      </div>
      <div style={{color:'#003311',fontSize:9,marginTop:8}}>github.com/EvezArt/evez-sim \u00b7 AGPL-3.0 \u00b7 @EVEZ666</div>
    </div>
  )
}

function ls(accent) {
  return {
    display:'block',background:'#001a08',border:'1px solid #003311',
    color:accent,padding:'12px 16px',borderRadius:4,textDecoration:'none',
    fontSize:12,fontWeight:'bold',
  }
}
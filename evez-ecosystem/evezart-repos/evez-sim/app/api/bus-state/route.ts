import { NextResponse } from 'next/server'

const GIST_ID = 'a6a6e78c59210c94828f8fa97f592ea7'
const GIST_URL = `https://api.github.com/gists/${GIST_ID}`

const CIRCUIT_REGISTRY = [
  { id:'hyperloop_r188', type:'fire_body', label:'R188 FIRE#35', description:'N=140 poly_c=0.566 V=7.240012 CEILING\u00d7106', poly_c:0.566183, omega_k:4, N:140, active:true, layer:'spine', truth_state:'final' },
  { id:'groq_synthesis', type:'fire_body', label:'Groq Synthesis Loop', description:'llama-3.3-70b \u00b7 30min cron \u00b7 tweet threads', poly_c:0.52, omega_k:3, N:120, active:true, layer:'game_server', truth_state:'final' },
  { id:'tts_voice', type:'fire_body', label:'TTS Voice Circuit', description:'OpenAI onyx tts-1-hd \u00b7 R-round narration', poly_c:0.51, omega_k:2, N:106, active:true, layer:'origin', truth_state:'final' },
  { id:'sms_circuit', type:'fire_body', label:'SMS Daily Update', description:'ClickSend \u00b7 8am PST \u00b7 +13076775504', poly_c:0.503, omega_k:2, N:110, active:true, layer:'client', truth_state:'final' },
  { id:'evez_sim_web', type:'fire_body', label:'evez-sim PWA', description:'Next.js \u00b7 Three.js \u00b7 Vercel \u00b7 LIVE', poly_c:0.58, omega_k:4, N:130, active:true, layer:'cdn', truth_state:'final' },
  { id:'fsc_engine', type:'fire_body', label:'FSC ENGINE', description:'Failure cartography \u00b7 BIAS CONSTITUTION \u00b7 \u03a9/\u03a3f scoring', poly_c:0.56, omega_k:3, N:126, active:true, layer:'game_server', truth_state:'final' },
  { id:'hypercomm_bus', type:'fire_body', label:'HYPERCOMM Bus', description:'Groq Node1 + Kimi-k2 Node2 + Synthesis Node3 \u00b7 2h cron', poly_c:0.554, omega_k:3, N:122, active:true, layer:'matchmaking', truth_state:'final' },
  { id:'jigsawstack_scanner', type:'topo_spider', label:'Jigsawstack Scanner', description:'Polymarket AI scrape ~2s \u00b7 needs JIGSAWSTACK_API_KEY secret', omega_k:2, N:141, active:true, layer:'origin', truth_state:'pending' },
  { id:'r189_no_fire', type:'topo_spider', label:'R189 NO-FIRE N=141=3\u00d747', description:'poly_c=0.433274 below threshold. V holds 7.240012. Void holds shape.', omega_k:2, N:141, active:true, layer:'spine', truth_state:'final' },
  { id:'r190_probe', type:'topo_spider', label:'R190 Probe N=142=2\u00d771', description:'omega_k=2 tau=4 \u00b7 fire TBD \u00b7 in-flight', omega_k:2, N:142, active:true, layer:'spine', truth_state:'pending' },
  { id:'masterbus_orchestrator', type:'topo_spider', label:'MasterBus Orchestrator', description:'SpawnBus+CapabilityBus+ValidatorBus+MetaBus \u00b7 GREEN last tick', omega_k:3, N:145, active:true, layer:'matchmaking', truth_state:'pending' },
  { id:'actions_block', type:'prime_void', label:'Actions Block', description:'PayPal enterprise billing failure \u00b7 evez-agentnet blocked \u00b7 fix: github.com/enterprises/evez/billing', N:89, active:true, layer:'auth', truth_state:'pending' },
  { id:'twitter_bearer_wall', type:'prime_void', label:'Twitter Bearer Token', description:'Hard human gate \u00b7 CAPTCHA + rate-limit wall \u00b7 cannot be automated', N:97, active:true, layer:'auth', truth_state:'pending' },
  { id:'gumroad_ssn', type:'prime_void', label:'Gumroad SSN Gate', description:'Payout blocked \u00b7 SSN required \u00b7 $0 revenue despite ZIPs live', N:101, active:true, layer:'origin', truth_state:'pending' },
  { id:'google_pw_compromised', type:'prime_void', label:'Google PW Compromised', description:'Password compromised 2026-02-24 \u00b7 needs manual rotation', N:83, active:true, layer:'auth', truth_state:'pending' },
]

async function readGistState(): Promise<Record<string, unknown> | null> {
  try {
    const r = await fetch(GIST_URL, { headers:{'User-Agent':'evez-sim/0.1.0'}, next:{revalidate:30} } as RequestInit)
    if (!r.ok) return null
    const data = await r.json() as { files: Record<string, { content: string }> }
    const f = data.files['hyperloop_state.json'] || data.files['activity_feed.json']
    if (f) return JSON.parse(f.content) as Record<string, unknown>
    return null
  } catch { return null }
}

export async function GET() {
  const gist_data = await readGistState()
  const V_global = (gist_data?.V as number) ?? 7.240012
  const current_round = (gist_data?.current_round as number) ?? 189
  const fire_count = (gist_data?.fire_count as number) ?? 35
  const spine_length = (gist_data?.spine_length as number) ?? 3848
  const res = {
    entities: CIRCUIT_REGISTRY,
    circuit_health: 'YELLOW',
    V_global, current_round, fire_count, spine_length,
    fires:   CIRCUIT_REGISTRY.filter(e=>e.type==='fire_body').length,
    voids:   CIRCUIT_REGISTRY.filter(e=>e.type==='prime_void').length,
    spiders: CIRCUIT_REGISTRY.filter(e=>e.type==='topo_spider').length,
    last_updated: new Date().toISOString(),
  }
  return NextResponse.json(res, { headers:{'Cache-Control':'public, s-maxage=30, stale-while-revalidate=60','Access-Control-Allow-Origin':'*'} })
}

export async function POST(request: Request) {
  const delta = await request.json() as Record<string, unknown>
  return NextResponse.json({ ok:true, op:delta['op']??'upsert', id:delta['id'], ts:new Date().toISOString() })
}
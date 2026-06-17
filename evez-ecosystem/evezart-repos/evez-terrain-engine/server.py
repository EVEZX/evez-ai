#!/usr/bin/env python3
"""
EVEZ Terrain Engine — Self-Hosted 3D Physics Map (No API Keys)
Procedural terrain with Perlin noise, mesh generation, textures, snapshot/rewind
Port 8897
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import math, hashlib, json, time, os, threading
from collections import OrderedDict
from typing import Optional
from datetime import datetime

app = FastAPI(title="EVEZ Terrain Engine", version="1.0.0")

SNAPSHOT_DIR = "/tmp/evez-terrain-snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# PERLIN NOISE (from scratch, no deps)
# ═══════════════════════════════════════════════════════════════
def _fade(t): return t * t * t * (t * (t * 6 - 15) + 10)
def _lerp(t, a, b): return a + t * (b - a)

GRAD2 = [(1,1),(-1,1),(1,-1),(-1,-1),(1,0),(-1,0),(0,1),(0,-1)]

def _grad(h, x, y):
    g = GRAD2[h & 7]
    return g[0] * x + g[1] * y

def _make_perm(seed: int):
    p = list(range(256))
    rng = seed
    for i in range(255, 0, -1):
        rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
        j = rng % (i + 1)
        p[i], p[j] = p[j], p[i]
    return p + p  # double for wrapping

def perlin2d(x, y, perm):
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255
    xf = x - math.floor(x)
    yf = y - math.floor(y)
    u = _fade(xf)
    v = _fade(yf)
    aa = perm[perm[xi] + yi]
    ab = perm[perm[xi] + yi + 1]
    ba = perm[perm[xi + 1] + yi]
    bb = perm[perm[xi + 1] + yi + 1]
    return _lerp(v,
        _lerp(u, _grad(aa, xf, yf), _grad(ba, xf - 1, yf)),
        _lerp(u, _grad(ab, xf, yf - 1), _grad(bb, xf - 1, yf - 1))
    )

def fbm(x, y, perm, octaves=6, lacunarity=2.0, gain=0.5):
    """Fractal Brownian Motion — multi-octave terrain"""
    val = 0.0
    amp = 1.0
    freq = 1.0
    mx = 0.0
    for _ in range(octaves):
        val += amp * perlin2d(x * freq, y * freq, perm)
        mx += amp
        amp *= gain
        freq *= lacunarity
    return val / mx

def seed_from_coords(lat, lng):
    return int(hashlib.sha256(f"{lat:.6f},{lng:.6f}".encode()).hexdigest()[:8], 16)

# ═══════════════════════════════════════════════════════════════
# SNAPSHOT/REWIND (same pattern as digital-twin-3d)
# ═══════════════════════════════════════════════════════════════
class SnapshotStore:
    def __init__(self, max=1000):
        self._s = OrderedDict()
        self._lock = threading.Lock()
        self._max = max
    def capture(self, sid, state):
        ts = int(time.time() * 1000)
        k = f"{sid}:{ts}:{hashlib.md5(json.dumps(state,sort_keys=True).encode()).hexdigest()[:8]}"
        with self._lock:
            self._s[k] = {"id":k,"scene":sid,"ts":ts,"state":state,"created":datetime.now().isoformat()}
            if len(self._s) > self._max: self._s.popitem(last=False)
            with open(f"{SNAPSHOT_DIR}/{k.replace(':','_')}.json",'w') as f: json.dump(self._s[k],f)
        return k
    def get(self, k):
        with self._lock: return self._s.get(k)
    def list_all(self, sid=None):
        with self._lock: snaps = list(self._s.values())
        if sid: snaps = [s for s in snaps if s["scene"]==sid]
        return snaps[-100:]
    def rewind(self, k):
        s = self.get(k)
        if not s:
            fp = f"{SNAPSHOT_DIR}/{k.replace(':','_')}.json"
            if os.path.exists(fp):
                with open(fp) as f: s = json.load(f)
        return s

store = SnapshotStore()

# ═══════════════════════════════════════════════════════════════
# PRESET SCENES
# ═══════════════════════════════════════════════════════════════
SCENES = {
    "desert-hot-springs": {
        "name": "Desert Hot Springs, CA",
        "lat": 33.9625, "lng": -116.5078, "zoom": 14,
        "terrain_scale": 1200, "water_level": 0.1, "biome": "desert"
    },
    "lake-mills-iowa": {
        "name": "Lake Mills, Iowa",
        "lat": 43.4180, "lng": -93.5347, "zoom": 14,
        "terrain_scale": 400, "water_level": 0.3, "biome": "plains"
    },
    "pacific-coast": {
        "name": "Pacific Coast Highway",
        "lat": 34.0195, "lng": -118.4912, "zoom": 13,
        "terrain_scale": 800, "water_level": 0.25, "biome": "coastal"
    },
    "rocky-mountains": {
        "name": "Rocky Mountains",
        "lat": 39.7392, "lng": -104.9903, "zoom": 12,
        "terrain_scale": 3500, "water_level": 0.15, "biome": "mountain"
    }
}

# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status":"ok","version":"1.0.0","service":"evez-terrain-engine","ts":int(time.time())}

@app.get("/")
def root():
    return {
        "service":"EVEZ Terrain Engine — Self-Hosted 3D Physics Map",
        "version":"1.0.0","port":8897,
        "no_api_keys_required": True,
        "features":["Perlin noise terrain","FBM multi-octave","3D mesh gen","Procedural textures",
                    "Snapshot/rewind","Three.js viewer","4 preset scenes"],
        "scenes": list(SCENES.keys()),
        "endpoints":["/health","/scene","/elevation/{lat}/{lng}","/mesh/{z}/{x}/{y}",
                     "/texture/{z}/{x}/{y}","/snapshot","/snapshots","/rewind/{id}","/viewer"]
    }

@app.get("/scene")
def list_scenes():
    return {"scenes": SCENES, "default": "desert-hot-springs"}

@app.get("/scene/{scene_id}")
def get_scene(scene_id: str):
    if scene_id not in SCENES:
        return {"error":f"scene {scene_id} not found","available":list(SCENES.keys())}
    snap = store.capture(scene_id, SCENES[scene_id])
    return {"scene": SCENES[scene_id], "snapshot": snap}

@app.get("/elevation/{lat}/{lng}")
def get_elevation(lat: float, lng: float):
    """Deterministic procedural elevation — no API key needed"""
    seed = seed_from_coords(lat, lng)
    perm = _make_perm(seed)
    # Scale to realistic range based on latitude
    h = fbm(lng * 0.01, lat * 0.01, perm, octaves=6)
    # Map to meters (sea level ~0, peaks ~4000m)
    elevation = h * 2000 + 500
    # Water bodies
    is_water = elevation < 0
    return {
        "lat": round(lat, 6), "lng": round(lng, 6),
        "elevation_m": round(elevation, 1),
        "is_water": is_water,
        "terrain_type": "water" if is_water else ("mountain" if elevation > 2000 else "plains" if elevation < 500 else "hills"),
        "seed": seed, "source": "procedural-perlin-fbm"
    }

@app.get("/mesh/{z}/{x}/{y}")
def get_mesh(z: int, x: int, y: int):
    """Generate a 3D terrain tile mesh"""
    seed = seed_from_coords(x, y)
    perm = _make_perm(seed)
    size = 16  # grid resolution
    scale = 1.0 / (2 ** z) if z > 0 else 1.0
    vertices, normals, uvs, indices, colors = [], [], [], [], []
    for j in range(size + 1):
        for i in range(size + 1):
            wx = (x + i / size) * scale
            wy = (y + j / size) * scale
            h = fbm(wx * 4, wy * 4, perm, octaves=5) * 2
            vertices.extend([i / size, h, j / size])
            normals.extend([0.0, 1.0, 0.0])  # simplified
            uvs.extend([i / size, j / size])
            # Procedural color
            if h < -0.2:
                colors.extend([0.1, 0.3, 0.8])  # water blue
            elif h < 0.0:
                colors.extend([0.9, 0.85, 0.6])  # sand
            elif h < 0.5:
                colors.extend([0.2, 0.6, 0.2])  # grass
            elif h < 1.0:
                colors.extend([0.5, 0.35, 0.2])  # rock
            else:
                colors.extend([0.95, 0.95, 0.98])  # snow
    # Index buffer (triangles)
    for j in range(size):
        for i in range(size):
            v0 = j * (size + 1) + i
            v1 = v0 + 1
            v2 = v0 + (size + 1)
            v3 = v2 + 1
            indices.extend([v0, v2, v1, v1, v2, v3])
    return {"vertices": vertices, "normals": normals, "uvs": uvs,
            "indices": indices, "colors": colors,
            "tile": {"z": z, "x": x, "y": y, "size": size}}

@app.get("/texture/{z}/{x}/{y}")
def get_texture(z: int, x: int, y: int):
    """Procedural texture data for a terrain tile"""
    seed = seed_from_coords(x, y)
    perm = _make_perm(seed)
    h = fbm(x * 0.1, y * 0.1, perm, octaves=4) * 2
    if h < -0.2:
        return {"type": "water", "rgb": [25, 76, 204], "hex": "#194C9C"}
    elif h < 0.0:
        return {"type": "sand", "rgb": [230, 217, 153], "hex": "#E6D999"}
    elif h < 0.5:
        return {"type": "grass", "rgb": [51, 153, 51], "hex": "#339933"}
    elif h < 1.0:
        return {"type": "rock", "rgb": [128, 89, 51], "hex": "#805933"}
    else:
        return {"type": "snow", "rgb": [242, 242, 250], "hex": "#F2F2FA"}

# ── Snapshot & Rewind ─────────────────────────────────────────
@app.post("/snapshot")
def create_snapshot(body: dict = {}):
    sid = body.get("scene", "desert-hot-springs")
    state = body.get("state", {"lat": 33.9625, "lng": -116.5078})
    k = store.capture(sid, state)
    return {"snapshot_id": k, "scene": sid, "ts": int(time.time() * 1000)}

@app.get("/snapshots")
def list_snapshots(scene: str = None):
    return {"snapshots": store.list_all(scene)}

@app.get("/rewind/{snap_id}")
def rewind(snap_id: str):
    s = store.rewind(snap_id)
    if not s: return {"error": f"snapshot {snap_id} not found"}
    return {"rewound_to": s, "state_restored": True, "timestamp": s["created"]}

# ── Three.js Procedural Globe Viewer ─────────────────────────
@app.get("/viewer", response_class=HTMLResponse)
def viewer():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html><head><title>EVEZ Terrain Engine — Procedural 3D Map</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;overflow:hidden;font-family:monospace;color:#0f0}
#info{position:absolute;top:10px;left:10px;z-index:99;background:rgba(0,0,0,.85);padding:15px;border-radius:8px;max-width:320px;border:1px solid #0f0}
#info h2{color:#0ff;margin:0 0 8px}
#info .s{color:#0f0;margin:4px 0;cursor:pointer;padding:4px;border-radius:4px}
#info .s:hover{background:#0f02}
#ctrl{position:absolute;bottom:10px;right:10px;z-index:99;background:rgba(0,0,0,.85);padding:12px;border-radius:8px;border:1px solid #0ff}
#ctrl button{background:#0ff;color:#000;border:0;padding:6px 16px;margin:3px;cursor:pointer;border-radius:4px;font-family:monospace;font-weight:bold}
#ctrl button:hover{background:#0cc}
#stats{position:absolute;bottom:10px;left:10px;z-index:99;background:rgba(0,0,0,.85);padding:10px;border-radius:8px;color:#0ff;font-size:11px}
canvas{display:block}
</style></head><body>
<div id="info">
  <h2>⚡ EVEZ Terrain Engine</h2>
  <div>Procedural 3D Map — No API Keys</div>
  <hr style="border-color:#0f0;opacity:.3;margin:8px 0">
  <div style="font-size:12px;margin-bottom:6px">SCENES:</div>
  <div class="s" onclick="loadScene('desert-hot-springs')">🏜️ Desert Hot Springs, CA</div>
  <div class="s" onclick="loadScene('lake-mills-iowa')">🌾 Lake Mills, Iowa</div>
  <div class="s" onclick="loadScene('pacific-coast')">🌊 Pacific Coast</div>
  <div class="s" onclick="loadScene('rocky-mountains')">🏔️ Rocky Mountains</div>
</div>
<div id="ctrl">
  <button onclick="capture()">📸 Capture</button>
  <button onclick="rewind()">⏪ Rewind</button>
  <button onclick="regen()">🔄 Regenerate</button>
</div>
<div id="stats">Loading...</div>

<script>
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x0a0a0a, 0.015);
const camera = new THREE.PerspectiveCamera(60, innerWidth/innerHeight, 0.1, 500);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(devicePixelRatio);
document.body.appendChild(renderer.domElement);

camera.position.set(12, 10, 12);
camera.lookAt(0, 0, 0);

// Orbit controls (manual)
let isDragging=false, prevX=0, prevY=0, rotY=0, rotX=0.6, dist=18;
renderer.domElement.addEventListener('mousedown',e=>{isDragging=true;prevX=e.clientX;prevY=e.clientY});
renderer.domElement.addEventListener('mousemove',e=>{
  if(!isDragging)return;
  rotY+=(e.clientX-prevX)*0.005;
  rotX+=(e.clientY-prevY)*0.005;
  rotX=Math.max(-1.2,Math.min(1.2,rotX));
  prevX=e.clientX;prevY=e.clientY;
  updateCamera();
});
renderer.domElement.addEventListener('mouseup',()=>isDragging=false);
renderer.domElement.addEventListener('wheel',e=>{dist+=e.deltaY*0.01;dist=Math.max(3,Math.min(60,dist));updateCamera()});
renderer.domElement.addEventListener('touchstart',e=>{if(e.touches.length===1){isDragging=true;prevX=e.touches[0].clientX;prevY=e.touches[0].clientY}});
renderer.domElement.addEventListener('touchmove',e=>{
  if(!isDragging||e.touches.length!==1)return;
  rotY+=(e.touches[0].clientX-prevX)*0.005;
  rotX+=(e.touches[0].clientY-prevY)*0.005;
  rotX=Math.max(-1.2,Math.min(1.2,rotX));
  prevX=e.touches[0].clientX;prevY=e.touches[0].clientY;
  updateCamera();
});
renderer.domElement.addEventListener('touchend',()=>isDragging=false);

function updateCamera(){
  camera.position.set(Math.sin(rotY)*Math.cos(rotX)*dist, Math.sin(rotX)*dist, Math.cos(rotY)*Math.cos(rotX)*dist);
  camera.lookAt(0,0,0);
}
updateCamera();

// Terrain generation in JS (matching server-side Perlin)
function fade(t){return t*t*t*(t*(t*6-15)+10)}
function lerp(t,a,b){return a+t*(b-a)}
const G=[[1,1],[-1,1],[1,-1],[-1,-1],[1,0],[-1,0],[0,1],[0,-1]];
function grad(h,x,y){const g=G[h&7];return g[0]*x+g[1]*y}
function mkPerm(seed){
  const p=Array.from({length:256},(_,i)=>i);
  let r=seed;
  for(let i=255;i>0;i--){r=(r*1103515245+12345)&0x7FFFFFFF;const j=r%(i+1);[p[i],p[j]]=[p[j],p[i]]}
  return p.concat(p);
}
function perlin2d(x,y,perm){
  const xi=Math.floor(x)&255,yi=Math.floor(y)&255,xf=x-Math.floor(x),yf=y-Math.floor(y);
  const u=fade(xf),v=fade(yf);
  const aa=perm[perm[xi]+yi],ab=perm[perm[xi]+yi+1],ba=perm[perm[xi+1]+yi],bb=perm[perm[xi+1]+yi+1];
  return lerp(v,lerp(u,grad(aa,xf,yf),grad(ba,xf-1,yf)),lerp(u,grad(ab,xf,yf-1),grad(bb,xf-1,yf-1)));
}
function fbm(x,y,perm,oct=6){let v=0,a=1,f=1,m=0;for(let i=0;i<oct;i++){v+=a*perlin2d(x*f,y*f,perm);m+=a;a*=0.5;f*=2}return v/m}

// Build terrain
let terrainMesh, currentSeed=42;
const SIZE=32, SCALE=16;

function buildTerrain(seed, scale=1.0){
  if(terrainMesh)scene.remove(terrainMesh);
  const perm=mkPerm(seed);
  const geo=new THREE.BufferGeometry();
  const pos=[],col=[],idx=[],norm=[];
  for(let j=0;j<=SIZE;j++)for(let i=0;i<=SIZE;i++){
    const u=i/SIZE,v=j/SIZE;
    const h=fbm(u*4*scale,v*4*scale,perm,6)*2*scale;
    pos.push((u-0.5)*SCALE, h, (v-0.5)*SCALE);
    norm.push(0,1,0);
    if(h<-0.2)col.push(0.1,0.3,0.8);
    else if(h<0)col.push(0.9,0.85,0.6);
    else if(h<0.5)col.push(0.2,0.6,0.2);
    else if(h<1)col.push(0.5,0.35,0.2);
    else col.push(0.95,0.95,0.98);
  }
  for(let j=0;j<SIZE;j++)for(let i=0;i<SIZE;i++){
    const a=j*(SIZE+1)+i,b=a+1,c=a+(SIZE+1),d=c+1;
    idx.push(a,c,b,b,c,d);
  }
  geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  geo.setAttribute('normal',new THREE.Float32BufferAttribute(norm,3));
  geo.setAttribute('color',new THREE.Float32BufferAttribute(col,3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const mat=new THREE.MeshPhongMaterial({vertexColors:true,flatShading:true,shininess:10});
  terrainMesh=new THREE.Mesh(geo,mat);
  scene.add(terrainMesh);
  // Water plane
  const wg=new THREE.PlaneGeometry(SCALE*1.5,SCALE*1.5);
  const wm=new THREE.MeshPhongMaterial({color:0x1a5276,transparent:true,opacity:0.7,side:THREE.DoubleSide});
  const water=new THREE.Mesh(wg,wm);
  water.rotation.x=-Math.PI/2;water.position.y=-0.2;
  scene.add(water);
}

// Lighting
scene.add(new THREE.AmbientLight(0x333344,0.6));
const sun=new THREE.DirectionalLight(0xffeedd,1.2);
sun.position.set(10,15,8);scene.add(sun);
scene.add(new THREE.HemisphereLight(0x446688,0x223311,0.4));

// Grid
const grid=new THREE.GridHelper(20,20,0x0f02,0x0f01);
grid.position.y=-2;scene.add(grid);

buildTerrain(currentSeed);

// Scene presets
const SCENES={
  'desert-hot-springs':{seed:37041723,scale:1.2,name:'Desert Hot Springs'},
  'lake-mills-iowa':{seed:439871,scale:0.5,name:'Lake Mills'},
  'pacific-coast':{seed:78012,scale:0.9,name:'Pacific Coast'},
  'rocky-mountains':{seed:104990,scale:2.0,name:'Rocky Mountains'}
};
function loadScene(id){
  const s=SCENES[id];if(!s)return;
  currentSeed=s.seed;buildTerrain(s.seed,s.scale);
  document.getElementById('stats').textContent='🗺️ '+s.name+' | Seed: '+s.seed;
}
// Init with default
document.getElementById('stats').textContent='🏜️ Desert Hot Springs | Seed: 37041723';

// Snapshots
let snaps=[];
function capture(){
  const state={seed:currentSeed,cam:{x:camera.position.x,y:camera.position.y,z:camera.position.z},ts:Date.now()};
  fetch('/snapshot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:'terrain',state})})
    .then(r=>r.json()).then(d=>{snaps.push({...state,snapId:d.snapshot_id});document.getElementById('stats').textContent+=' 📸'});
}
function rewind(){
  if(!snaps.length){document.getElementById('stats').textContent='No snapshots';return}
  const last=snaps[snaps.length-1];
  fetch('/rewind/'+last.snapId).then(r=>r.json()).then(d=>{
    if(d.rewound_to){
      const s=d.rewound_to.state;
      currentSeed=s.seed;buildTerrain(s.seed);
      if(s.cam)camera.position.set(s.cam.x,s.cam.y,s.cam.z);
      document.getElementById('stats').textContent='⏪ Rewound to '+d.timestamp;
    }
  });
}
function regen(){
  currentSeed=Math.floor(Math.random()*99999999);
  buildTerrain(currentSeed);
  document.getElementById('stats').textContent='🔄 New terrain | Seed: '+currentSeed;
}

// Render loop
function animate(){
  requestAnimationFrame(animate);
  if(terrainMesh)terrainMesh.rotation.y+=0.0005;
  renderer.render(scene,camera);
}
animate();
window.addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
</script></body></html>
""")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8897)

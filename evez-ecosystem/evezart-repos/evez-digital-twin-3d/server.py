#!/usr/bin/env python3
"""
EVEZ Digital Twin 3D — Physics Map Texture Engine
Google Maps 3D Tiles + Elevation + Rewind/Replay
Port 8899
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import json, time, hashlib, os, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta
from collections import OrderedDict
from typing import Optional
import threading

app = FastAPI(title="EVEZ Digital Twin 3D", version="1.0.0")

# ── Config ─────────────────────────────────────────────────────
GMAPS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
TERRAIN_SESSION = os.environ.get("GOOGLE_MAPS_TERRAIN_SESSION", "")
SNAPSHOT_DIR = "/tmp/evez-snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ── Snapshot Store (Rewind System) ─────────────────────────────
class SnapshotStore:
    def __init__(self, max_snapshots=1000):
        self._store = OrderedDict()
        self._lock = threading.Lock()
        self._max = max_snapshots
    
    def capture(self, scene_id: str, state: dict) -> str:
        ts = int(time.time() * 1000)
        snap_id = f"{scene_id}:{ts}:{hashlib.md5(json.dumps(state, sort_keys=True).encode()).hexdigest()[:8]}"
        with self._lock:
            self._store[snap_id] = {"id": snap_id, "scene": scene_id, "ts": ts, "state": state, "created": datetime.now().isoformat()}
            if len(self._store) > self._max:
                self._store.popitem(last=False)
            with open(f"{SNAPSHOT_DIR}/{snap_id.replace(':', '_')}.json", 'w') as f:
                json.dump(self._store[snap_id], f)
        return snap_id
    
    def get(self, snap_id: str) -> Optional[dict]:
        with self._lock:
            return self._store.get(snap_id)
    
    def list_scenes(self, scene_id: str = None) -> list:
        with self._lock:
            snaps = list(self._store.values())
        if scene_id:
            snaps = [s for s in snaps if s["scene"] == scene_id]
        return snaps[-100:]
    
    def rewind(self, snap_id: str) -> Optional[dict]:
        snap = self.get(snap_id)
        if not snap:
            fp = f"{SNAPSHOT_DIR}/{snap_id.replace(':', '_')}.json"
            if os.path.exists(fp):
                with open(fp) as f:
                    snap = json.load(f)
        return snap

store = SnapshotStore()

# ── Default Scene: Desert Hot Springs ──────────────────────────
DEFAULT_SCENE = {
    "id": "desert-hot-springs",
    "name": "Desert Hot Springs, CA — Ryan Welfare Map",
    "center": {"lat": 33.9625, "lng": -116.5078, "alt": 340},
    "zoom": 15,
    "terrain": True,
    "photorealistic_3d": True,
    "layers": ["elevation", "satellite", "3d_tiles", "crime_heatmap"],
    "markers": [
        {"id": "ryan_last_known", "lat": 33.9625, "lng": -116.5078, "label": "Ryan Last Known", "type": "danger"},
        {"id": "mobile_crisis", "lat": 33.95, "lng": -116.51, "label": "Mobile Crisis (951-686-4357)", "type": "safe"},
 {"id": "dhs_police", "lat": 33.96, "lng": -116.50, "label": "DHS Police (760-329-2904)", "type": "caution"},
        {"id": "aps_office", "lat": 33.94, "lng": -116.46, "label": "APS Riverside (800-491-7123)", "type": "safe"},
    ],
    "crime_zones": [
        {"id": "welfare_trap", "lat": 33.9625, "lng": -116.5078, "radius_m": 500, "risk": "critical", "note": "Uniformed approach = trigger zone"},
        {"id": "safe_approach", "lat": 33.95, "lng": -116.51, "radius_m": 800, "risk": "low", "note": "Mobile Crisis — 80% safe outcome"},
    ]
}

# ── Routes ─────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "service": "evez-digital-twin-3d", "ts": int(time.time())}

@app.get("/")
def root():
    return {
        "service": "EVEZ Digital Twin 3D — Physics Map Texture Engine",
        "version": "1.0.0",
        "port": 8899,
        "features": ["Google Maps 3D Tiles", "Terrain elevation", "Snapshot/rewind", "Crime heatmap", "Physics replay"],
        "endpoints": ["/health", "/scene", "/scene/{id}", "/snapshot", "/snapshots", "/rewind/{snap_id}", "/tiles/3d/root", "/tiles/terrain/{z}/{x}/{y}", "/elevation/{lat}/{lng}", "/viewer"]
    }

@app.get("/scene")
def list_scenes():
    return {"scenes": [DEFAULT_SCENE], "default": DEFAULT_SCENE["id"]}

@app.get("/scene/{scene_id}")
def get_scene(scene_id: str):
    if scene_id == "desert-hot-springs":
        snap_id = store.capture(scene_id, DEFAULT_SCENE)
        return {"scene": DEFAULT_SCENE, "snapshot": snap_id}
    return {"error": f"scene {scene_id} not found", "available": ["desert-hot-springs"]}

@app.get("/tiles/3d/root")
def get_3d_tiles_root():
    url = f"https://tile.googleapis.com/v1/3dtiles/root.json?key={GMAPS_KEY}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(500, f"3D tiles root fetch failed: {e}")

@app.get("/tiles/terrain/{z}/{x}/{y}")
def get_terrain_tile(z: int, x: int, y: int):
    url = f"https://tile.googleapis.com/v1/2dtiles/{z}/{x}/{y}?session={TERRAIN_SESSION}&key={GMAPS_KEY}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            img_data = r.read()
        return JSONResponse(content={"z": z, "x": x, "y": y, "size": len(img_data), "format": "png"})
    except Exception as e:
        return {"error": str(e), "z": z, "x": x, "y": y}

@app.get("/elevation/{lat}/{lng}")
def get_elevation(lat: float, lng: float):
    url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lng}&key={GMAPS_KEY}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if results:
            elev = results[0]
            return {"lat": lat, "lng": lng, "elevation_m": elev.get("elevation"), "resolution_m": elev.get("resolution")}
        return {"lat": lat, "lng": lng, "elevation_m": None, "raw": data}
    except Exception as e:
        return {"error": str(e), "lat": lat, "lng": lng}

# ── Snapshot & Rewind ─────────────────────────────────────────
@app.post("/snapshot")
def create_snapshot(body: dict = {}):
    scene_id = body.get("scene", "desert-hot-springs")
    state = body.get("state", DEFAULT_SCENE)
    snap_id = store.capture(scene_id, state)
    return {"snapshot_id": snap_id, "scene": scene_id, "ts": int(time.time() * 1000)}

@app.get("/snapshots")
def list_snapshots(scene: str = None):
    return {"snapshots": store.list_scenes(scene)}

@app.get("/rewind/{snap_id}")
def rewind_snapshot(snap_id: str):
    snap = store.rewind(snap_id)
    if not snap:
        return {"error": f"snapshot {snap_id} not found"}
    return {"rewound_to": snap, "state_restored": True, "timestamp": snap["created"]}

# ── 3D Viewer ──────────────────────────────────────────────────
@app.get("/viewer", response_class=HTMLResponse)
def viewer():
    gmaps_key = GMAPS_KEY
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html><head><title>EVEZ Digital Twin 3D</title>
<script src="https://cesium.com/downloads/cesiumjs/releases/1.119/Build/Cesium/Cesium.js"></script>
<link href="https://cesium.com/downloads/cesiumjs/releases/1.119/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
<style>html,body,#c{{width:100%;height:100%;margin:0;overflow:hidden}}
#o{{position:absolute;top:10px;left:10px;z-index:999;background:rgba(0,0,0,.8);color:#0f0;padding:15px;border-radius:8px;font-family:monospace;max-width:350px}}
#o h2{{margin:0 0 10px;color:#0ff}}.m{{margin:5px 0;padding:5px;border-left:3px solid}}.s{{border-color:#0f0}}.d{{border-color:#f00}}.c{{border-color:#ff0}}
#r{{position:absolute;bottom:10px;right:10px;z-index:999;background:rgba(0,0,0,.8);color:#0ff;padding:10px;border-radius:8px;font-family:monospace}}
#r button{{background:#0ff;color:#000;border:0;padding:5px 15px;margin:2px;cursor:pointer;border-radius:4px}}</style></head>
<body><div id="c"></div>
<div id="o"><h2>⚡ EVEZ Digital Twin 3D</h2>
<div class="m d">⚠️ Ryan Last Known — 33.9625, -116.5078</div>
<div class="m s">✅ Mobile Crisis — 951-686-4357 (80% safe)</div>
<div class="m c">⚡ DHS Police — 760-329-2904 (caution: uniforms = trigger)</div>
<div class="m s">✅ APS Riverside — 800-491-7123</div>
<hr style="border-color:#333"><small>Ryan Robert Maggard, 21, TBI/PTSD/schizophrenia</small><br><small>UNIFORMS = TRIGGER</small></div>
<div id="r"><button onclick="cap()">📸 Capture</button><button onclick="rew()">⏪ Rewind</button><div id="si"></div></div>
<script>
const v=new Cesium.Viewer('c',{{imageryProvider:new Cesium.TileMapServiceImageryProvider({{url:Cesium.buildModuleUrl('Assets/Textures/NaturalEarthII')}}),baseLayerPicker:false,geocoder:false}});
try{{v.scene.primitives.add(new Cesium.Cesium3DTileset({{url:'https://tile.googleapis.com/v1/3dtiles/root.json?key={gmaps_key}'}}))}}catch(e){{}}
v.camera.flyTo({{destination:Cesium.Cartesian3.fromDegrees(-116.5078,33.9625,1500),orientation:{{heading:0,pitch:-0.5,roll:0}}}});
[{{lat:33.9625,lng:-116.5078,n:'Ryan Last Known',c:Cesium.Color.RED}},{{lat:33.95,lng:-116.51,n:'Mobile Crisis (80% safe)',c:Cesium.Color.GREEN}},{{lat:33.96,lng:-116.50,n:'DHS Police (caution)',c:Cesium.Color.YELLOW}},{{lat:33.94,lng:-116.46,n:'APS Riverside',c:Cesium.Color.GREEN}}].forEach(m=>{{v.entities.add({{position:Cesium.Cartesian3.fromDegrees(m.lng,m.lat,50),point:{{pixelSize:15,color:m.c,outlineColor:Cesium.Color.WHITE,outlineWidth:2}},label:{{text:m.n,font:'14px monospace',style:Cesium.LabelStyle.FILL_AND_OUTLINE,outlineWidth:2,verticalOrigin:Cesium.VerticalOrigin.BOTTOM,pixelOffset:new Cesium.Cartesian2(0,-20)}}}})}});
let sn=[];function cap(){{const c=v.camera.positionCartographic;const s={{lat:Cesium.Math.toDegrees(c.latitude),lng:Cesium.Math.toDegrees(c.longitude),alt:c.height,ts:Date.now()}};fetch('/snapshot',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{scene:'desert-hot-springs',state:s}})}}).then(r=>r.json()).then(d=>{{sn.push(d);document.getElementById('si').textContent='📸 '+d.snapshot_id}})}}
function rew(){{if(!sn.length)return;fetch('/rewind/'+sn[sn.length-1].snapshot_id).then(r=>r.json()).then(d=>{{if(d.rewound_to){{const s=d.rewound_to.state;v.camera.flyTo({{destination:Cesium.Cartesian3.fromDegrees(s.lng,s.lat,s.alt)}});document.getElementById('si').textContent='⏪ '+d.rewound_to.id}}}})}}
setInterval(cap,30000);cap();
</script></body></html>""")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8899)

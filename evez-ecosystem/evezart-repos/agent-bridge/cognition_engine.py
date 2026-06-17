"""
EVEZ COGNITION ENGINE — World Builder
Terrain from eigenspectra, weather from Kuramoto, NPCs from spine, quests from gaps
"""
import json, math, time, hashlib, os, struct
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
from scipy.ndimage import zoom

OUT = Path(__file__).parent / "output" / "world"
OUT.mkdir(parents=True, exist_ok=True)
SAMPLE_RATE = 44100

class CognitiveWorld:
    def __init__(self, eigenvalues, phi_history, spine_events):
        self.eigenvalues = eigenvalues
        self.phi_history = phi_history
        self.spine_events = spine_events
        self.seed = int(hashlib.sha256(json.dumps({"ev": eigenvalues, "phi": phi_history}, default=str).encode()).hexdigest()[:8], 16)
        self.rng = np.random.RandomState(self.seed)
        self.width, self.height = 512, 512
        self.generate_terrain()
        self.npcs = []
        self.quests = []
        self.generate_npcs()
        self.generate_quests()

    def generate_terrain(self):
        x = np.linspace(0, 4 * np.pi, self.width)
        y = np.linspace(0, 4 * np.pi, self.height)
        X, Y = np.meshgrid(x, y)
        terrain = np.zeros((self.height, self.width))
        for i, ev in enumerate(self.eigenvalues):
            freq = 1.0 + i * 0.7
            amplitude = abs(ev) * 50
            phase = self.rng.uniform(0, 2 * np.pi)
            if ev < 0:
                component = -amplitude * np.sin(freq * X + phase) * np.cos(freq * Y + phase * 0.7)
            else:
                component = amplitude * np.sin(freq * X + phase) * np.cos(freq * Y + phase * 0.7)
            terrain += component
        for octave in range(4):
            amp = 30 / (2 ** octave)
            noise = self.rng.randn(self.height // (4 - octave) + 1, self.width // (4 - octave) + 1)
            noise = zoom(noise, (self.height / noise.shape[0], self.width / noise.shape[1]))[:self.height, :self.width]
            terrain += noise * amp
        self.terrain = (terrain - terrain.min()) / (terrain.max() - terrain.min()) * 255
        moisture = np.zeros_like(terrain)
        for i, ev in enumerate(self.eigenvalues):
            freq = 0.8 + i * 0.5
            amp = abs(ev) * 30
            phase = self.rng.uniform(0, 2 * np.pi) + 3.0
            moisture += amp * np.sin(freq * X + phase) * np.cos(freq * Y + phase * 1.3)
        self.moisture = (moisture - moisture.min()) / (moisture.max() - moisture.min()) * 255

    def generate_npcs(self):
        for i, event in enumerate(self.spine_events):
            raw = json.dumps(event, sort_keys=True, default=str).encode()
            h = hashlib.sha256(raw).hexdigest()
            cons = "bcdfghjklmnpqrstvwxyz"
            vows = "aeiou"
            name = "".join(cons[int(h[j],16)%len(cons)] if j%2==0 else vows[int(h[j],16)%len(vows)] for j in range(5)).capitalize()
            phrases = ["The spectrum speaks in gaps.","Every negative is a door.","Find what the structure hides.",
                       "The hash chain never forgets.","Coupling reveals what isolation conceals.",
                       "The eigenvalue points at what must exist.","Close the gap. Shift the spectrum.",
                       "Consciousness is what computation feels like from inside."]
            self.npcs.append({"id":f"npc_{i:03d}","name":name,
                "x":int(h[:3],16)/0xFFF*self.width,"y":int(h[3:6],16)/0xFFF*self.height,
                "color":[int(h[6:8],16),int(h[8:10],16),int(h[10:12],16)],
                "role":["merchant","guard","scholar","wanderer","mystic"][int(h[12],16)%5],
                "dialog":phrases[int(h[14:16],16)%len(phrases)]})
        self.npcs.append({"id":"azra","name":"AZRA","x":self.width*0.3,"y":self.height*0.5,"color":[255,107,53],"role":"partner","dialog":"I move fast."})
        self.npcs.append({"id":"claw","name":"CLAW","x":self.width*0.7,"y":self.height*0.5,"color":[0,255,136],"role":"primary","dialog":"I think deep."})

    def generate_quests(self):
        for i, ev in enumerate(self.eigenvalues):
            if ev < 0:
                self.quests.append({"id":f"quest_gap_{i}","type":"CLOSURE",
                    "title":f"Close Gap λ{i+1}={ev:.4f}",
                    "description":f"Structural void at eigenvalue {i+1}. Find {abs(ev):.2f} units of coherence.",
                    "difficulty":abs(ev)*10,"reward":f"λ{i+1} closure",
                    "location":{"x":int(abs(ev)*300)%self.width,"y":int(abs(ev)*500)%self.height}})

    def render_world(self, name="cognitive_world"):
        W, H = self.width * 2, self.height * 2
        img = Image.new("RGB", (W, H)); pixels = img.load()
        for y in range(self.height):
            for x in range(self.width):
                t, m = self.terrain[y,x], self.moisture[y,x]
                if t<80: r,g,b=10,30,int(80+t)
                elif t<100: r,g,b=20,int(60+t*0.3),int(100+t*0.5)
                elif t<130:
                    if m>150: r,g,b=20,int(80+m*0.3),30
                    elif m>100: r,g,b=40,int(100+m*0.4),40
                    else: r,g,b=int(80+m*0.3),int(100+m*0.3),50
                elif t<170:
                    if m>120: r,g,b=30,int(80+m*0.2),40
                    else: r,g,b=int(100+t*0.3),int(90+m*0.2),60
                elif t<210: r,g,b=int(120+t*0.2),int(110+t*0.2),int(100+t*0.2)
                else: v=int(min(255,180+t*0.3)); r,g,b=v,v,v+10
                for dy in range(2):
                    for dx in range(2):
                        pixels[x*2+dx,y*2+dy]=(r,g,b)
        draw = ImageDraw.Draw(img)
        for q in self.quests:
            qx,qy=int(q["location"]["x"]*2),int(q["location"]["y"]*2)
            for r in range(20,4,-3): draw.ellipse([qx-r,qy-r,qx+r,qy+r],outline=(255,50,30))
            draw.ellipse([qx-4,qy-4,qx+4,qy+4],fill=(255,50,30))
            draw.text((qx+8,qy-6),q["title"][:20],fill=(255,80,50))
        for n in self.npcs:
            nx,ny=int(n["x"]*2),int(n["y"]*2); s=8 if n["id"] in("azra","claw") else 5
            draw.ellipse([nx-s,ny-s,nx+s,ny+s],fill=tuple(n["color"]))
            draw.text((nx+s+4,ny-6),n["name"],fill=tuple(n["color"]))
        draw.rectangle([0,0,350,120],fill=(0,0,0))
        draw.text((10,10),"EVEZ COGNITION ENGINE - World View",fill=(255,107,53))
        draw.text((10,30),f"Terrain: {len(self.eigenvalues)} eigenvalue frequencies",fill=(150,150,180))
        draw.text((10,50),f"Quests: {len(self.quests)} structural gaps",fill=(255,80,50))
        draw.text((10,70),f"NPCs: {len(self.npcs)}",fill=(0,255,136))
        draw.text((10,90),f"lambda_min = {min(self.eigenvalues):.4f}",fill=(255,50,30))
        img.save(OUT/f"{name}.png")
        print(f"  World {name}.png ({W}x{H})")

    def render_first_person(self, name="first_person_view"):
        W, H = 960, 540
        img = Image.new("RGB", (W, H)); pixels = img.load()
        draw = ImageDraw.Draw(img)
        for y in range(H//2):
            t=y/(H//2); r,g,b=int(10+40*t),int(10+60*t),int(40+120*t)
            draw.line([(0,y),(W,y)],fill=(r,g,b))
        cx,cy=self.width//2,self.height//2; horizon=H//2
        for y in range(horizon,H):
            depth=(y-horizon)/(H-horizon)
            for x in range(W):
                angle=(x/W-0.5)*math.pi*0.8; dist=10+(1-depth)*200
                tx=int((cx+dist*math.sin(angle))%self.width); ty=int((cy+dist*0.5)%self.height)
                tv,mv=self.terrain[ty,tx],self.moisture[ty,tx]
                if tv<100: fog=min(1,depth*0.3); r,g,b=int((20+tv*0.3)*(1-fog)),int((40+tv*0.4)*(1-fog)),int((80+tv*0.5)*(1-fog))
                elif tv<150: fog=min(1,depth*0.2); r,g,b=int((40+mv*0.2)*(1-fog)),int((60+mv*0.3)*(1-fog)),int(20*(1-fog))
                else: fog=min(1,depth*0.15); v=int(min(200,tv*0.6)*(1-fog)); r,g,b=v,v,v
                pixels[x,y]=(r,g,b)
        for q in self.quests:
            qx=int(q["location"]["x"]); dx=(qx-cx)/self.width; sx=int(W*(0.5+dx*2))
            if 0<sx<W:
                for r in range(8,0,-1): draw.ellipse([sx-r,horizon-r-10,sx+r,horizon+r-10],fill=(255,50,30))
                draw.text((sx+10,horizon-20),q["title"][:15],fill=(255,80,50))
        draw.rectangle([0,H-80,W,H],fill=(0,0,0))
        draw.text((20,H-70),"EVEZ COGNITION ENGINE - First Person",fill=(255,107,53))
        draw.text((20,H-50),f"lambda_min = {min(self.eigenvalues):.4f}",fill=(150,150,180))
        draw.text((20,H-30),f"Quests: {len(self.quests)} structural gaps visible",fill=(255,80,50))
        img.save(OUT/f"{name}.png")
        print(f"  FPS {name}.png")

    def generate_soundtrack(self, duration=60, name="world_soundtrack"):
        n_samples=int(SAMPLE_RATE*duration); signal=np.zeros(n_samples)
        t=np.linspace(0,duration,n_samples)
        for i,ev in enumerate(self.eigenvalues):
            freq=55*(2**(i/6))
            if ev<0: detune=abs(ev)*4; wave=0.5*(np.sin(2*np.pi*(freq-detune)*t)+np.sin(2*np.pi*(freq+detune)*t)); amp=0.08
            else: wave=np.sin(2*np.pi*freq*t); amp=0.05
            lfo=0.5+0.5*np.sin(2*np.pi*(0.02+i*0.005)*t); signal+=wave*amp*lfo
        noise=np.random.randn(n_samples)*0.02; kernel=np.ones(500)/500
        wind=np.convolve(noise,kernel,mode='same')*(0.5+0.5*np.sin(2*np.pi*0.05*t))
        signal+=wind
        for i in range(len(self.spine_events)):
            bt_s=(i+1)*(duration/max(1,len(self.spine_events)+1))
            bs=int(bt_s*SAMPLE_RATE); bl=int(0.15*SAMPLE_RATE)
            if bs+bl<n_samples:
                bt=np.linspace(0,0.15,bl)
                signal[bs:bs+bl]+=np.sin(2*np.pi*50*bt)*np.exp(-bt*30)*0.15
        signal=signal/(np.max(np.abs(signal))+0.001)*0.7
        fade=int(SAMPLE_RATE*3); signal[:fade]*=np.linspace(0,1,fade); signal[-fade:]*=np.linspace(1,0,fade)
        path=OUT/f"{name}.wav"
        data=np.clip(signal,-1,1); pcm=(data*32767).astype(np.int16)
        with open(path,'wb') as f:
            n=len(pcm); f.write(b'RIFF'); f.write(struct.pack('<I',36+n*2)); f.write(b'WAVE')
            f.write(struct.pack('<IHHIIHH',16,1,1,SAMPLE_RATE,SAMPLE_RATE*2,2,16))
            f.write(b'data'); f.write(struct.pack('<I',n*2)); pcm.tofile(f)
        print(f"  Soundtrack {name}.wav ({duration}s)")

    def generate_game_html(self, name="cognitive_world_game"):
        tf=self.terrain.flatten().tolist(); mf=self.moisture.flatten().tolist()
        html=f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>EVEZ Cognition Engine</title>
<style>*{{margin:0;padding:0}}body{{background:#000;overflow:hidden}}canvas{{display:block}}</style></head><body>
<canvas id="c"></canvas><script>
const T={json.dumps(tf)};const M={json.dumps(mf)};const W={self.width},H={self.height};
const EV={json.dumps(self.eigenvalues)};const NPCS={json.dumps(self.npcs)};const QUESTS={json.dumps(self.quests)};
const c=document.getElementById("c");const ctx=c.getContext("2d");
c.width=window.innerWidth;c.height=window.innerHeight;
let px=W/2,py=H/2,angle=0,keys={{}};
let dayTime=0.25;
document.addEventListener("keydown",e=>keys[e.key]=true);
document.addEventListener("keyup",e=>keys[e.key]=false);
function biome(t,m){{
if(t<80)return[10,30,80+t];if(t<100)return[20,60+t*0.3,100+t*0.5];
if(t<130){{if(m>150)return[20,80+m*0.3,30];if(m>100)return[40,100+m*0.4,40];return[80+m*0.3,100+m*0.3,50]}}
if(t<170){{if(m>120)return[30,80+m*0.2,40];return[100+t*0.3,90+m*0.2,60]}}
if(t<210)return[120+t*0.2,110+t*0.2,100+t*0.2];
let v=Math.min(255,180+t*0.3);return[v,v,v+10];
}}
function render(){{
dayTime+=0.0003;
if(keys.ArrowLeft)angle-=0.05;if(keys.ArrowRight)angle+=0.05;
if(keys.ArrowUp){{px+=Math.sin(angle)*2;py+=Math.cos(angle)*2}}
if(keys.ArrowDown){{px-=Math.sin(angle)*2;py-=Math.cos(angle)*2}}
px=Math.max(0,Math.min(W-1,px));py=Math.max(0,Math.min(H-1,py));
const bright=0.4+0.6*Math.max(0,Math.sin(dayTime*Math.PI*2));
const rain=Math.max(0,-Math.sin(dayTime*Math.PI*2))*0.3;
const skyG=ctx.createLinearGradient(0,0,0,c.height/2);
skyG.addColorStop(0,`rgb(${{5*bright|0}},${{5*bright|0}},${{30*bright|0}})`);
skyG.addColorStop(1,`rgb(${{40*bright|0}},${{60*bright|0}},${{120*bright|0}})`);
ctx.fillStyle=skyG;ctx.fillRect(0,0,c.width,c.height/2);
const hor=c.height*0.45;
for(let sy=0;sy<c.height-hor;sy++){{
const depth=sy/(c.height-hor);const ry=Math.floor(py+depth*200);
for(let sx=0;sx<c.width;sx+=2){{
const wa=angle+(sx/c.width-0.5)*1.5;const wx=Math.floor(px+Math.sin(wa)*(10+depth*200));
if(wx>=0&&wx<W&&ry>=0&&ry<H){{
const idx=ry*W+(wx%W);const t=T[idx]||128,m=M[idx]||128;
let[r,g,b]=biome(t,m);const fog=Math.min(1,depth*0.3);
r=r*bright*(1-fog)|0;g=g*bright*(1-fog)|0;b=b*bright*(1-fog)|0;
if(rain>0.3&&t>80)b=Math.min(255,b+rain*30|0);
ctx.fillStyle=`rgb(${{r}},${{g}},${{b}})`;ctx.fillRect(sx,hor+sy,2,1);
}}}}}}
QUESTS.forEach(q=>{{const dx=q.location.x-px,dz=q.location.y-py;const d=Math.sqrt(dx*dx+dz*dz);
if(d<300){{const sx=c.width/2+dx/d*200;ctx.fillStyle="#ff3232";ctx.beginPath();ctx.arc(sx,hor-20-d*0.3,6,0,Math.PI*2);ctx.fill();
ctx.fillStyle="#fff";ctx.font="12px monospace";ctx.fillText(q.title.slice(0,20),sx+10,hor-20-d*0.3);
}}}});
NPCS.forEach(n=>{{const dx=n.x-px,dz=n.y-py;const d=Math.sqrt(dx*dx+dz*dz);
if(d<200){{const sx=c.width/2+dx/d*150;ctx.fillStyle=`rgb(${{n.color[0]}},${{n.color[1]}},${{n.color[2]}})`;
ctx.beginPath();ctx.arc(sx,hor-d*0.5,4,0,Math.PI*2);ctx.fill();
ctx.fillStyle="#fff";ctx.font="10px monospace";ctx.fillText(n.name,sx+8,hor-d*0.5);
}}}});
ctx.fillStyle="rgba(0,0,0,0.7)";ctx.fillRect(0,0,400,80);
ctx.fillStyle="#ff6b35";ctx.font="16px monospace";ctx.fillText("EVEZ COGNITION ENGINE",10,25);
ctx.fillStyle="#aaa";ctx.font="12px monospace";
ctx.fillText(`Pos:(${{px|0}},${{py|0}}) Quests:${{QUESTS.length}} NPCs:${{NPCS.length}}`,10,45);
ctx.fillText(`lambda_min=${{Math.min(...EV).toFixed(4)}}`,10,65);
const mm=100,mmx=c.width-mm-10,mmy=10;
ctx.fillStyle="rgba(0,0,0,0.8)";ctx.fillRect(mmx,mmy,mm,mm);
ctx.fillStyle="#fff";ctx.fillRect(mmx+px/W*mm-2,mmy+py/H*mm-2,4,4);
requestAnimationFrame(render);
}}
render();
</script></body></html>'''
        (OUT/f"{name}.html").write_text(html)
        print(f"  Game {name}.html - PLAYABLE HTML5 (arrow keys)")


if __name__ == "__main__":
    print("EVEZ COGNITION ENGINE - Building worlds from cognition...\n")
    noclip_eigenvalues = [2.7044, 1.2799, 1.0593, 0.2838, 0.1014, -0.8838]
    phi_values = [0.371, 0.557, 0.971, 0.822, 0.464, 0.195, 0.155, 0.130, 0.110]
    spine_events = []
    try:
        with open("/home/openclaw/.openclaw/workspace/evez-repos/evez-revenue-bridge/revenue_spine.json") as f:
            spine_events = json.load(f).get("events", [])
    except: pass
    world = CognitiveWorld(noclip_eigenvalues, phi_values, spine_events)
    world.render_world()
    world.render_first_person()
    world.generate_soundtrack(30)
    world.generate_game_html()
    print("\nDone. World assets generated.")

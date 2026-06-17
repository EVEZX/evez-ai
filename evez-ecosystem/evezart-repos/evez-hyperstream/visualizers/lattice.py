"""Reactive lattice — 8-node cross-stream neural mesh with pulse propagation"""
import numpy as np, matplotlib, time, math
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from io import BytesIO

N = 8
_adj = np.random.rand(N,N)*0.5+0.1; np.fill_diagonal(_adj,0)
_adj = (_adj+_adj.T)/2
_pulses = []
_NAMES = ["HyperGeo2D","HyperGeo3D","4DPolytope","Lattice","AIArena","Fractals","Fourier","EVEZ666"]

def mutate(c):
    node = abs(hash(c)) % N
    _pulses.append({"n":node,"t":time.time(),"v":min(2.0,len(c)/15.0+0.4)})

def render_frame(t):
    # Ambient auto-pulses
    if int(t*2)%3==0 and (not _pulses or time.time()-_pulses[-1]["t"]>1):
        mutate(f"auto{int(t)}")

    angles = np.linspace(0,2*np.pi,N,endpoint=False)
    pos = np.column_stack([np.cos(angles),np.sin(angles)])*0.72
    now = time.time()

    fig, ax = plt.subplots(figsize=(16,9),facecolor="#050510")
    ax.set_facecolor("#050510"); ax.set_xlim(-1.5,1.5); ax.set_ylim(-0.95,0.95)
    ax.set_aspect("equal"); ax.axis("off")
    fig.suptitle("EVEZ REACTIVE LATTICE  Cross-Stream Neural Mesh  LIVE",
                 color="#FF00FF",fontsize=16,fontweight="bold",y=0.97)

    for i in range(N):
        for j in range(i+1,N):
            p1,p2 = pos[i],pos[j]; w=_adj[i,j]
            ax.plot([p1[0],p2[0]],[p1[1],p2[1]],"-",color="#0d0d2e",lw=2*w,alpha=0.35)
            for pulse in _pulses:
                age = now-pulse["t"]
                if age>2.5: continue
                wp = p1+(p2-p1)*((age*0.45)%1.0)
                al = max(0,pulse["v"]*(1-age/2.0))
                ax.scatter(wp[0],wp[1],color="#FF00FF",s=28*al,alpha=al,zorder=6)

    for i,(px,py) in enumerate(pos):
        glow = 1.0+sum(p["v"]*(1-(now-p["t"])/1.5)
                       for p in _pulses if p["n"]==i and now-p["t"]<1.5)
        c = plt.cm.plasma(i/N)
        ax.scatter(px,py,color=c,s=180*min(glow,3),zorder=10,alpha=0.9)
        ax.scatter(px,py,color="white",s=22,zorder=11,alpha=0.75)
        lx=px*1.28; ly=py*1.28
        ax.text(lx,ly,_NAMES[i],color=c,fontsize=9,ha="center",va="center",fontweight="bold")

    # Clean old pulses
    _pulses[:] = [p for p in _pulses if now-p["t"]<3]

    ts = time.strftime("%H:%M:%S UTC",time.gmtime())
    fig.text(0.01,0.01,f"@lordevez  {ts}  {N} streams connected",color="#333",fontsize=8)
    fig.text(0.99,0.01,"Comments on any stream pulse the mesh",color="#333",fontsize=8,ha="right")
    plt.tight_layout(rect=[0,0.03,1,0.95])
    buf = BytesIO(); fig.savefig(buf,format="raw",dpi=120); plt.close(fig)
    buf.seek(0); return buf.read()

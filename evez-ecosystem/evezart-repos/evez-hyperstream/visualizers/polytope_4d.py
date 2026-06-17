"""4D polytope projection: tesseract, 24-cell, 16-cell — 6-plane rotation"""
import numpy as np, matplotlib, time, math
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from io import BytesIO

_shape = 0
_q = []

def mutate(c):
    cl = c.lower()
    if "tesseract" in cl or "cube" in cl: _q.append(0)
    elif "24" in cl: _q.append(1)
    elif "16" in cl or "cross" in cl: _q.append(2)
    else:
        import re
        n = re.findall(r"\d+", c)
        if n: _q.append(int(n[0])%3)

def R4(angles):
    pairs = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
    M = np.eye(4)
    for (i,j), a in zip(pairs, angles):
        G = np.eye(4); G[i,i]=math.cos(a); G[i,j]=-math.sin(a)
        G[j,i]=math.sin(a); G[j,j]=math.cos(a)
        M = M @ G
    return M

def tesseract():
    v = np.array([[i,j,k,l] for i in [-1,1] for j in [-1,1] for k in [-1,1] for l in [-1,1]], float)
    e = [(a,b) for a in range(16) for b in range(a+1,16) if np.sum(np.abs(v[a]-v[b])==2)==1]
    return v, e

def cell16():
    v = np.vstack([np.eye(4),-np.eye(4)]).astype(float)
    e = [(i,j) for i in range(8) for j in range(i+1,8) if abs(i-j)!=4]
    return v, e

def cell24():
    v = []
    for s1 in [-1,1]:
        for s2 in [-1,1]:
            for ax in range(4):
                for ax2 in range(4):
                    if ax!=ax2:
                        row = [0,0,0,0]; row[ax]=s1; row[ax2]=s2
                        if row not in v: v.append(row)
    v = np.array(v, float)
    norms = np.linalg.norm(v,axis=1,keepdims=True); v /= (norms+1e-9)
    e = [(i,j) for i in range(len(v)) for j in range(i+1,len(v))
         if 0.45 < abs(float(np.dot(v[i],v[j]))) < 0.56]
    return v, e

SHAPES = [tesseract, cell16, cell24]
NAMES = ["TESSERACT (8-cell)", "16-CELL (cross-polytope)", "24-CELL"]
COLORS = ["#FF6B35","#00FFD0","#FF00FF"]

def render_frame(t):
    global _shape
    if _q: _shape = _q.pop(0)
    si = _shape % 3
    angles = [t*0.18, t*0.12, t*0.08, t*0.10, t*0.15, t*0.07]
    R = R4(angles)
    v, edges = SHAPES[si]()
    rv = (R @ v.T).T
    w4 = 2.0/(3.0 - rv[:,3]+1e-9)
    pXY = rv[:,:2]*w4[:,None]
    pXZ = np.column_stack([rv[:,0], rv[:,2]])*w4[:,None]

    fig, axes = plt.subplots(1,2,figsize=(16,9),facecolor="#050510")
    fig.suptitle(f"4D POLYTOPE  {NAMES[si]}  6-PLANE ROTATION",
                 color=COLORS[si], fontsize=14, fontweight="bold", y=0.97)

    for ax, proj, plane in [(axes[0],pXY,"XY"),(axes[1],pXZ,"XZ")]:
        ax.set_facecolor("#050510"); ax.set_xlim(-2.2,2.2); ax.set_ylim(-2.2,2.2)
        for ea,eb in edges:
            c = plt.cm.plasma(0.3+0.5*w4[ea])
            al = max(0.1, min(0.9, 1-np.linalg.norm(proj[ea]-proj[eb])*0.1))
            ax.plot([proj[ea,0],proj[eb,0]],[proj[ea,1],proj[eb,1]],
                    color=c, lw=1.3, alpha=al)
        for vi,(px,py) in enumerate(proj):
            ax.scatter(px,py,color=plt.cm.plasma(0.3+0.5*w4[vi]),s=16,zorder=5,alpha=0.85)
        ax.set_title(f"Projection: {plane}-plane", color=COLORS[si], fontsize=11)
        ax.set_xlabel("x",color="#555"); ax.set_ylabel(plane[1],color="#555")
        ax.tick_params(colors="#333")
        for sp in ax.spines.values(): sp.set_edgecolor("#1a1a2e")
        ax.grid(color="#111",alpha=0.3)

    ts = time.strftime("%H:%M:%S UTC",time.gmtime())
    fig.text(0.01,0.01,f"@lordevez  {ts}  evezstation.vercel.app",color="#333",fontsize=8)
    fig.text(0.99,0.01,"Type: tesseract / 24 / 16  to switch",color="#333",fontsize=8,ha="right")
    plt.tight_layout(rect=[0,0.03,1,0.95])
    buf = BytesIO(); fig.savefig(buf,format="raw",dpi=120); plt.close(fig)
    buf.seek(0); return buf.read()

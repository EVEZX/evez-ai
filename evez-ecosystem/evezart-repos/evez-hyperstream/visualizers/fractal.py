"""Mandelbrot/Julia comment-reactive fractal zoom"""
import numpy as np, matplotlib, time
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from io import BytesIO

_cx, _cy = -0.5, 0.0
_zoom = 1.0
_jc = complex(-0.4, 0.6)
_mode = "mandelbrot"
_q = []

def mutate(c):
    import re; cl=c.lower()
    if "julia" in cl: _q.append({"m":"julia"})
    elif "mandel" in cl: _q.append({"m":"mandelbrot"})
    n=re.findall(r"-?\d+\.?\d*",c)
    if len(n)>=2: _q.append({"cx":float(n[0]),"cy":float(n[1]),"z":0.4})

def mset(c,it=96):
    z=np.zeros_like(c); M=np.zeros(c.shape,int)
    for i in range(it):
        m=np.abs(z)<=2; z[m]=z[m]**2+c[m]; M[m&(np.abs(z)>2)]=i
    return M

def julia(z,c,it=96):
    M=np.zeros(z.shape,int)
    for i in range(it):
        m=np.abs(z)<=2; z[m]=z[m]**2+c; M[m&(np.abs(z)>2)]=i
    return M

def render_frame(t):
    global _cx,_cy,_zoom,_jc,_mode
    if _q:
        q=_q.pop(0)
        if "m" in q: _mode=q["m"]
        if "cx" in q: _cx=q["cx"]; _cy=q["cy"]; _zoom=q.get("z",0.5)
    _zoom*=0.9992
    if _zoom<5e-5: _zoom=1.0; _cx,_cy=-0.5,0.0
    W,H=1280,720
    x=np.linspace(_cx-_zoom,_cx+_zoom,W)
    y=np.linspace(_cy-_zoom*H/W,_cy+_zoom*H/W,H)
    X,Y=np.meshgrid(x,y); C=X+1j*Y
    if _mode=="julia":
        _jc=-0.4+0.6j+0.08*np.exp(1j*t*0.018)
        M=julia(C.copy(),_jc)
    else:
        M=mset(C)
    fig,ax=plt.subplots(figsize=(16,9),facecolor="#000005")
    ax.set_facecolor("#000005")
    ax.imshow(M,cmap="inferno",origin="lower",extent=[x[0],x[-1],y[0],y[-1]],interpolation="bilinear")
    ax.set_xlabel("Re",color="#444"); ax.set_ylabel("Im",color="#444")
    ax.tick_params(colors="#222")
    for sp in ax.spines.values(): sp.set_edgecolor("#0d0d1a")
    ms=f"JULIA c={_jc:.3f}" if _mode=="julia" else "MANDELBROT SET"
    fig.suptitle(f"EVEZ FRACTALS  {ms}  zoom={1/_zoom:.1e}",
                 color="#FF6B35",fontsize=15,fontweight="bold",y=0.97)
    ts=time.strftime("%H:%M:%S UTC",time.gmtime())
    fig.text(0.01,0.01,f"@lordevez  {ts}  evezstation.vercel.app",color="#333",fontsize=8)
    fig.text(0.99,0.01,"Type coords or julia/mandel",color="#333",fontsize=8,ha="right")
    plt.tight_layout(rect=[0,0.03,1,0.95])
    buf=BytesIO(); fig.savefig(buf,format="raw",dpi=120); plt.close(fig)
    buf.seek(0); return buf.read()

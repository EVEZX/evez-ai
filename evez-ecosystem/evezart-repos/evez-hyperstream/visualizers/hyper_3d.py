"""Hypergeometric 3D surface visualizer — rotating complex plane"""
import numpy as np, matplotlib, time
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
from scipy.special import hyp2f1
from io import BytesIO

_a, _b, _c = 0.5, 0.3, 1.5
_q = []

def mutate(comment):
    import re
    n = [float(x) for x in re.findall(r"-?\d+\.?\d*", comment)][:3]
    if n: _q.append(n)

def render_frame(t):
    global _a, _b, _c
    if _q:
        n = _q.pop(0)
        _a = max(0.1, min(1.8, abs(n[0])%1.8+0.1))
        if len(n)>1: _b = max(0.1, min(1.8, abs(n[1])%1.8+0.1))
        if len(n)>2: _c = max(0.5, min(3.0, abs(n[2])%3.0+0.5))

    a = _a + 0.2*np.sin(t*0.04); b = _b + 0.15*np.cos(t*0.03)
    u = np.linspace(0, 0.88, 55); v = np.linspace(0, 2*np.pi, 55)
    U, V = np.meshgrid(u, v)
    Zc = U * np.exp(1j*V)
    try:
        F = hyp2f1(a, b, _c, Zc.ravel())
    except Exception:
        F = np.ones(Zc.size)
    Amp = np.log1p(np.abs(F).reshape(U.shape))
    X = U*np.cos(V); Y = U*np.sin(V)

    fig = plt.figure(figsize=(16,9), facecolor="#050510")
    ax = fig.add_subplot(111, projection="3d", facecolor="#050510")
    norm = Amp / (Amp.max()+1e-9)
    surf = ax.plot_surface(X, Y, Amp, facecolors=plt.cm.plasma(norm),
                           linewidth=0, antialiased=True, alpha=0.92)
    elev = 18 + 18*np.sin(t*0.02)
    ax.view_init(elev=elev, azim=t*0.35 % 360)
    ax.set_facecolor("#050510")
    ax.tick_params(colors="#222")
    ax.set_xlabel("Re(z)", color="#444", labelpad=3)
    ax.set_ylabel("Im(z)", color="#444", labelpad=3)
    ax.set_zlabel("|2F1|", color="#444", labelpad=3)
    for p in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
        p.fill=False; p.set_edgecolor("#0d0d1a")
    ax.grid(color="#0d0d1a", alpha=0.4)

    ts = time.strftime("%H:%M:%S UTC", time.gmtime())
    fig.text(0.5, 0.96, f"2F1({a:.2f},{b:.2f};{_c:.2f};z)  HYPERGEOMETRIC 3D SURFACE",
             ha="center", color="#00FFD0", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.01, f"@lordevez  {ts}  evezstation.vercel.app", color="#333", fontsize=8)
    fig.text(0.99, 0.01, "Type numbers to mutate a,b,c", color="#333", fontsize=8, ha="right")
    plt.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="raw", dpi=120); plt.close(fig)
    buf.seek(0); return buf.read()

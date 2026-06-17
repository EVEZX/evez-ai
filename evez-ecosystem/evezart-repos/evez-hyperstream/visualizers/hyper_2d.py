"""Hypergeometric 2D visualizer — 2F1(a,b;c;z) phase portraits, comment-reactive"""
import numpy as np, matplotlib, time
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.special import hyp2f1
from io import BytesIO

_params = {"a": 0.5, "b": 0.3, "c": 1.2}
_q = []

def mutate(comment):
    import re
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", comment)][:3]
    if nums: _q.append(nums)

def render_frame(t):
    global _params
    if _q:
        n = _q.pop(0)
        _params["a"] = max(0.1, min(1.9, abs(n[0]) % 1.9 + 0.1))
        if len(n)>1: _params["b"] = max(0.1, min(1.9, abs(n[1]) % 1.9 + 0.1))
        if len(n)>2: _params["c"] = max(0.5, min(3.0, abs(n[2]) % 3.0 + 0.5))

    a = _params["a"] + 0.25 * np.sin(t * 0.04)
    b = _params["b"] + 0.15 * np.cos(t * 0.03)
    c = _params["c"]

    x = np.linspace(-0.93, 0.93, 360)
    y = np.linspace(-0.93, 0.93, 360)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j*Y
    mask = np.abs(Z) < 0.93
    vals = np.zeros_like(Z, dtype=complex)
    try:
        vals[mask] = hyp2f1(a, b, c, Z[mask].ravel())
    except Exception:
        pass

    fig, axes = plt.subplots(1, 2, figsize=(16,9), facecolor="#050510")
    fig.suptitle(f"2F1({a:.2f},{b:.2f};{c:.2f};z)  HYPERGEOMETRIC PHASE PORTRAIT",
                 color="#00FFD0", fontsize=15, fontweight="bold", y=0.97)

    phase = np.angle(vals); phase[~mask] = np.nan
    amp = np.log1p(np.abs(vals)); amp[~mask] = np.nan

    ax1 = axes[0]; ax1.set_facecolor("#050510")
    ax1.imshow(phase, cmap="hsv", origin="lower", extent=[-1,1,-1,1], vmin=-np.pi, vmax=np.pi)
    th = np.linspace(0,2*np.pi,200)
    ax1.plot(np.cos(th), np.sin(th), "w-", lw=0.4, alpha=0.3)
    ax1.set_title("Phase angle(2F1)", color="#00FFD0", fontsize=11)
    ax1.set_xlabel("Re(z)", color="#666"); ax1.set_ylabel("Im(z)", color="#666")
    ax1.tick_params(colors="#444")
    for sp in ax1.spines.values(): sp.set_edgecolor("#1a1a2e")

    ax2 = axes[1]; ax2.set_facecolor("#050510")
    ax2.imshow(amp, cmap="inferno", origin="lower", extent=[-1,1,-1,1])
    for r in [0.25, 0.5, 0.75, 0.9]:
        al = 0.2 + 0.2*np.sin(t*0.08 + r*6)
        ax2.plot(r*np.cos(th), r*np.sin(th), "c-", lw=0.7, alpha=al)
    ax2.set_title("Amplitude log|2F1|", color="#00FFD0", fontsize=11)
    ax2.set_xlabel("Re(z)", color="#666"); ax2.set_ylabel("Im(z)", color="#666")
    ax2.tick_params(colors="#444")
    for sp in ax2.spines.values(): sp.set_edgecolor("#1a1a2e")

    ts = time.strftime("%H:%M:%S UTC", time.gmtime())
    fig.text(0.01, 0.01, f"@lordevez  EVEZ Station  {ts}  evezstation.vercel.app", color="#333", fontsize=8)
    fig.text(0.99, 0.01, "Type numbers to mutate parameters", color="#333", fontsize=8, ha="right")
    plt.tight_layout(rect=[0,0.03,1,0.95])
    buf = BytesIO(); fig.savefig(buf, format="raw", dpi=120); plt.close(fig)
    buf.seek(0); return buf.read()

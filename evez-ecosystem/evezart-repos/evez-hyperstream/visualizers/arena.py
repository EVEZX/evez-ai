"""AI Arena — CodeKlaw vs AnalystKlaw vs CreativeKlaw vs ShieldKlaw live battle"""
import numpy as np, matplotlib, time, random
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from io import BytesIO

AGENTS = [
    {"name":"CodeKlaw",    "color":"#00FF88","score":100.0},
    {"name":"AnalystKlaw", "color":"#FF6B35","score":100.0},
    {"name":"CreativeKlaw","color":"#FF00FF","score":100.0},
    {"name":"ShieldKlaw",  "color":"#00D4FF","score":100.0},
]
_hist = {a["name"]:[100.0] for a in AGENTS}
_votes = {a["name"]:0.0 for a in AGENTS}
_q = []

def mutate(c):
    cl=c.lower()
    for a in AGENTS:
        if a["name"].lower().replace("klaw","") in cl:
            _q.append(a["name"])

def render_frame(t):
    if _q:
        v=_q.pop(0); _votes[v]+=1
    for a in AGENTS:
        a["score"] = max(5, min(999, a["score"] + random.gauss(0,0.7) + _votes[a["name"]]*0.04))
        _votes[a["name"]] = max(0, _votes[a["name"]]-0.008)
        _hist[a["name"]].append(a["score"])
        if len(_hist[a["name"]])>250: _hist[a["name"]].pop(0)

    fig, axes = plt.subplots(1,2,figsize=(16,9),facecolor="#050510",
                             gridspec_kw={"width_ratios":[1,1.6]})
    fig.suptitle("EVEZ AI ARENA  LIVE SKILLSET BATTLE",
                 color="#FFAA00",fontsize=16,fontweight="bold",y=0.97)

    ax1=axes[0]; ax1.set_facecolor("#050510")
    names=[a["name"] for a in AGENTS]; scores=[a["score"] for a in AGENTS]
    colors=[a["color"] for a in AGENTS]
    bars=ax1.barh(names,scores,color=colors,alpha=0.85,height=0.6)
    for bar,score,col in zip(bars,scores,colors):
        ax1.text(bar.get_width()+4, bar.get_y()+bar.get_height()/2,
                 f"{score:.0f}", va="center", color=col, fontsize=11, fontweight="bold")
    ax1.set_xlim(0,max(scores)*1.3+50)
    ax1.set_xlabel("Arena Score",color="#888"); ax1.set_title("LIVE SCORES",color="#FFAA00",fontsize=12)
    ax1.tick_params(colors="#555")
    for sp in ax1.spines.values(): sp.set_edgecolor("#1a1a2e")

    ax2=axes[1]; ax2.set_facecolor("#050510")
    for a in AGENTS:
        ax2.plot(_hist[a["name"]],color=a["color"],lw=1.8,label=a["name"],alpha=0.88)
    ax2.set_title("SCORE HISTORY",color="#FFAA00",fontsize=12)
    ax2.set_xlabel("Frames",color="#888"); ax2.set_ylabel("Score",color="#888")
    ax2.legend(facecolor="#111",edgecolor="#333",labelcolor="white",fontsize=9,loc="upper left")
    ax2.tick_params(colors="#555")
    for sp in ax2.spines.values(): sp.set_edgecolor("#1a1a2e")
    ax2.grid(color="#111",alpha=0.3)

    leader=max(AGENTS,key=lambda a:a["score"])
    fig.text(0.5,0.03,f"LEADING: {leader['name']}  ({leader['score']:.0f} pts)  Type name to vote!",
             ha="center",color=leader["color"],fontsize=12,fontweight="bold")

    ts=time.strftime("%H:%M:%S UTC",time.gmtime())
    fig.text(0.01,0.008,f"@lordevez  {ts}",color="#333",fontsize=8)
    plt.tight_layout(rect=[0,0.06,1,0.95])
    buf=BytesIO(); fig.savefig(buf,format="raw",dpi=120); plt.close(fig)
    buf.seek(0); return buf.read()

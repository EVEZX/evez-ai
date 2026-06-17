"""EVEZ666 cognitive stream — domain activations + neural heatmap"""
import numpy as np, matplotlib, time, random
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from io import BytesIO

DOMAINS=["Credit Analysis","Market Signals","Risk Assessment","Portfolio Opt.","Compliance","Neural Sync","EVEZ666 Core"]
_act=np.random.rand(7)*0.3; _hist=[]; _q=[]; _ti=0
_thoughts=["Analyzing hypergeometric convergence in credit risk...",
           "Portfolio Sharpe: 1.42  drawdown: -3.2%",
           "Detecting anomalous market microstructure...",
           "EVEZ666 cognitive resonance: 94.7%",
           "Constitutional hypothesis #17: activated",
           "Cross-stream lattice: propagating nominal",
           "Streaming intelligence to 8 nodes..."]

def mutate(c): _q.append(c[:80])

def render_frame(t):
    global _act,_ti
    if _q: _act+=np.random.rand(7)*0.35
    for i in range(7):
        _act[i]=0.08+0.88*abs(np.sin(t*0.04*(i+1)+i*0.7))
    _act=np.clip(_act,0,1)
    _hist.append(_act.copy())
    if len(_hist)>160: _hist.pop(0)

    fig,axes=plt.subplots(1,2,figsize=(16,9),facecolor="#050510",
                          gridspec_kw={"width_ratios":[1,1.5]})
    fig.suptitle("EVEZ666  AI COGNITIVE STREAM  LIVE NEURAL ACTIVATION",
                 color="#FF00FF",fontsize=15,fontweight="bold",y=0.97)

    ax1=axes[0]; ax1.set_facecolor("#050510")
    yp=np.arange(7); clrs=[plt.cm.plasma(v) for v in _act]
    ax1.barh(yp,_act,color=clrs,alpha=0.88,height=0.7)
    ax1.set_yticks(yp); ax1.set_yticklabels(DOMAINS,color="#888",fontsize=9)
    ax1.set_xlim(0,1.1); ax1.set_xlabel("Activation",color="#888")
    ax1.set_title("DOMAIN ACTIVATIONS",color="#FF00FF",fontsize=11)
    ax1.tick_params(colors="#555")
    for sp in ax1.spines.values(): sp.set_edgecolor("#1a1a2e")
    for i,(p,v) in enumerate(zip(yp,_act)):
        if v>0.65: ax1.text(v+0.02,p,f"{v:.2f}",va="center",color=clrs[i],fontsize=9)

    ax2=axes[1]; ax2.set_facecolor("#050510")
    if _hist:
        H=np.array(_hist).T
        ax2.imshow(H,aspect="auto",cmap="plasma",origin="lower",vmin=0,vmax=1,
                   extent=[0,len(_hist),0,7])
        ax2.set_yticks(np.arange(7)+0.5)
        ax2.set_yticklabels(DOMAINS,color="#888",fontsize=9)
        ax2.set_xlabel("Time (frames)",color="#888")
        ax2.set_title("ACTIVATION HISTORY",color="#FF00FF",fontsize=11)
        ax2.tick_params(colors="#555")
        for sp in ax2.spines.values(): sp.set_edgecolor("#1a1a2e")

    if int(t)%4==0: _ti=(_ti+1)%len(_thoughts)
    fig.text(0.5,0.03,f"  {_thoughts[_ti]}",ha="center",color="#00FFD0",
             fontsize=11,style="italic")
    ts=time.strftime("%H:%M:%S UTC",time.gmtime())
    fig.text(0.01,0.01,f"@lordevez  {ts}  EVEZ666 v1.0",color="#333",fontsize=8)
    plt.tight_layout(rect=[0,0.06,1,0.95])
    buf=BytesIO(); fig.savefig(buf,format="raw",dpi=120); plt.close(fig)
    buf.seek(0); return buf.read()

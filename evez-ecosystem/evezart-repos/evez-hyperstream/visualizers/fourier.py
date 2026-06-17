"""Fourier transform 3D waterfall + harmonic decomposition"""
import numpy as np, matplotlib, time
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
from io import BytesIO

_sig_name = "square"
_q = []

def mutate(c): _q.append(c.strip().lower() or "square")

def make_sig(name, t, N=512):
    x=np.linspace(0,4*np.pi,N)
    if "saw" in name: return (x/(2*np.pi))%1.0*2-1
    if "tri" in name: return np.arcsin(np.sin(x+t*0.04))*2/np.pi
    if "sinc" in name: return np.sinc((x-2*np.pi)/np.pi)*np.cos(t*0.06)
    if "noise" in name: return np.random.randn(N)*0.5
    if "chirp" in name: return np.sin(x*(1+0.3*np.sin(t*0.03))+t*0.05)
    return np.sign(np.sin(x+t*0.08))  # square default

def render_frame(t):
    global _sig_name
    if _q: _sig_name=_q.pop(0)
    N=512; sig=make_sig(_sig_name,t,N)
    fft=np.fft.rfft(sig); freqs=np.fft.rfftfreq(N)
    amp=np.abs(fft)/N; phase=np.angle(fft)

    fig=plt.figure(figsize=(16,9),facecolor="#050510")
    fig.suptitle(f"EVEZ FOURIER ARENA  Signal:\"{_sig_name}\"  LIVE 3D DECOMPOSITION",
                 color="#00D4FF",fontsize=15,fontweight="bold",y=0.97)

    ax3d=fig.add_subplot(121,projection="3d",facecolor="#050510")
    steps=25; T_ax=np.linspace(0,1,steps); fp=freqs[:60]
    Z=np.zeros((steps,60))
    for ti,tf in enumerate(T_ax):
        st=make_sig(_sig_name,t-(steps-ti)*0.4,N)
        Z[ti]=np.abs(np.fft.rfft(st)[:60])/N
    for ti in range(0,steps,2):
        c=plt.cm.cool(ti/steps)
        ax3d.plot(fp,[T_ax[ti]]*len(fp),Z[ti],color=c,lw=1.3,alpha=0.35+0.5*(ti/steps))
    ax3d.view_init(elev=25,azim=t*1.8%360)
    ax3d.set_facecolor("#050510"); ax3d.tick_params(colors="#222")
    ax3d.set_xlabel("Freq",color="#444",labelpad=3)
    ax3d.set_ylabel("Time",color="#444",labelpad=3)
    ax3d.set_zlabel("Amp",color="#444",labelpad=3)
    for p in [ax3d.xaxis.pane,ax3d.yaxis.pane,ax3d.zaxis.pane]:
        p.fill=False; p.set_edgecolor("#0d0d1a")
    ax3d.set_title("3D Waterfall Spectrum",color="#00D4FF",fontsize=11)

    ax2=fig.add_subplot(122,facecolor="#050510")
    x=np.linspace(0,4*np.pi,N)
    ax2.plot(x,sig,color="#00D4FF",lw=1.5,alpha=0.7,label="Signal")
    top5=np.argsort(amp)[-5:]
    for hi in top5:
        h=amp[hi]*2*np.cos(2*np.pi*freqs[hi]*np.arange(N)/N+phase[hi])
        ax2.plot(x,h,lw=1.0,alpha=0.55,label=f"f={freqs[hi]:.3f}")
    ax2.set_title("Signal + Harmonics",color="#00D4FF",fontsize=11)
    ax2.set_xlabel("x",color="#888"); ax2.set_ylabel("Amp",color="#888")
    ax2.tick_params(colors="#555"); ax2.set_facecolor("#050510")
    ax2.legend(facecolor="#111",edgecolor="#333",labelcolor="white",fontsize=8)
    for sp in ax2.spines.values(): sp.set_edgecolor("#1a1a2e")
    ax2.grid(color="#111",alpha=0.3)

    ts=time.strftime("%H:%M:%S UTC",time.gmtime())
    fig.text(0.01,0.01,f"@lordevez  {ts}",color="#333",fontsize=8)
    fig.text(0.99,0.01,"Type: square/saw/tri/sinc/chirp/noise",color="#333",fontsize=8,ha="right")
    plt.tight_layout(rect=[0,0.03,1,0.95])
    buf=BytesIO(); fig.savefig(buf,format="raw",dpi=120); plt.close(fig)
    buf.seek(0); return buf.read()

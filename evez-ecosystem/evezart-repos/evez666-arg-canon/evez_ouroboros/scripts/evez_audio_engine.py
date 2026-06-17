# EVEZ Phonkstep Casino Bloop Egyptian Wheel Audio Engine v1.0
# 160 BPM | Egyptian pentatonic (D E F# A B) | 8 recursive generations
# FM synthesis + 808 kicks + casino bloops + FIRE/NOFIRE contrast
# See evez_sound_daemon.py for the always-on reasoning layer

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
import warnings
warnings.filterwarnings('ignore')

SR=44100; BPM=160; BEAT=SR*60//BPM; BAR=BEAT*4; GENS=8; BARS_PER=2
DUR=GENS*BARS_PER*BAR
EGYPTIAN=[38,40,42,45,47,50,52,54,57,59,62,64,66,69,71]
EGYPT_HZ=[440*(2**((m-69)/12)) for m in EGYPTIAN]

def sine(f,d,a=0.5,p=0): t=np.linspace(0,d/SR,d,endpoint=False); return a*np.sin(2*np.pi*f*t+p)
def saw(f,d,a=0.4): t=np.linspace(0,d/SR,d,endpoint=False); return a*(2*((t*f)%1)-1)
def noise(d,a=0.1): return a*(np.random.rand(d)*2-1)
def env(d,a=0.01,dc=0.05,s=0.7,r=0.1):
    e=np.ones(d)*s; as_=min(int(a*SR),d); ds_=min(int(dc*SR),d-as_); rs_=min(int(r*SR),d)
    e[:as_]=np.linspace(0,1,as_); e[as_:as_+ds_]=np.linspace(1,s,ds_)
    if rs_>0: e[-rs_:]=np.linspace(s,0,rs_)
    return e
def lpf(s,c,o=4): b,a=butter(o,min(c/(SR/2),0.99),btype='low'); return lfilter(b,a,s)
def hpf(s,c,o=2): b,a=butter(o,max(c/(SR/2),0.001),btype='high'); return lfilter(b,a,s)
def dist(s,d=3): return np.tanh(s*d)/np.tanh(d)
def rev(s,ms=40,dc=0.4): d=int(ms*SR/1000); o=s.copy(); (o.__setitem__(slice(d,None),o[d:]+s[:-d]*dc)) if d<len(s) else None; return o
def stut(s,n=8,p=0.3,seed=42):
    rng=np.random.RandomState(seed); c=len(s)//n; o=s.copy()
    for i in range(n):
        if rng.rand()<p:
            st=i*c; en=st+c
            if en<=len(s): o[st:en]=s[st:en][::-1]
    return o
def pbend(s,c=50): f=2**(c/1200); ix=np.clip(np.arange(len(s))/f,0,len(s)-1).astype(int); return s[ix][:len(s)]
def kick(d=None):
    if d is None: d=BEAT
    t=np.linspace(0,d/SR,d,endpoint=False)
    return dist(np.sin(2*np.pi*np.cumsum(np.exp(-t*30)*80+40)/SR)*np.exp(-t*12)*0.9,2.5)
def snare(d=None):
    if d is None: d=BEAT//2
    t=np.linspace(0,d/SR,d,endpoint=False)
    return lpf((noise(d,0.6)+0.3*np.sin(2*np.pi*200*t)*np.exp(-t*40))*np.exp(-t*20),8000)
def hat(d=None,op=False):
    if d is None: d=BEAT//4
    t=np.linspace(0,d/SR,d,endpoint=False)
    return hpf(noise(d,0.3)*np.exp(-t*(1 if op else 5)),6000)
def bloop(hz,d,det=15,ly=3):
    s=np.zeros(d)
    for i in range(ly): s+=sine(hz*(2**((i-ly//2)*det/1200)),d,0.25)*env(d,0.002,0.04,0,0.05)
    return pbend(s,np.random.uniform(-80,80))
def arp(gi,sp=0,bars=2):
    d=bars*BAR; s=np.zeros(d); sd=max(BEAT//(2+gi),SR//20)
    for i,p in enumerate(range(0,d,sd)):
        f=EGYPT_HZ[(i+gi*3)%len(EGYPT_HZ)]; ep=sp+i*0.17*gi; e=min(p+sd,d); cd=e-p
        t=np.linspace(0,cd/SR,cd,endpoint=False)
        s[p:e]+=(np.sin(2*np.pi*f*t+(1.5+gi*0.3)*np.sin(2*np.pi*f*0.5*t+ep)))*env(cd,0.005,0.03,0.6,0.08)*0.4
    return s
def fire_layer(d,f=True):
    if f:
        s=noise(d,0.4)
        for hz in [55,82.5,110]: s+=saw(hz,d,0.25)
        return lpf(dist(s,4),3000)
    s=np.zeros(d)
    for hz in [EGYPT_HZ[0],EGYPT_HZ[4],EGYPT_HZ[9]]: s+=sine(hz,d,0.12)*env(d,0.3,0.2,0.5,0.4)
    return rev(s,80,0.5)[::-1][:d]
def grid(bars=2,gi=0):
    d=bars*BAR; s=np.zeros(d); rng=np.random.RandomState(gi*31)
    for bar in range(bars):
        base=bar*BAR
        for bp in [0,2*BEAT,int(2.5*BEAT)]:
            k=kick(); e=min(base+bp+len(k),d); c=e-(base+bp)
            if c>0: s[base+bp:e]+=k[:c]
        for bp in [BEAT,3*BEAT]:
            sn=snare(); e=min(base+bp+len(sn),d); c=e-(base+bp)
            if c>0: s[base+bp:e]+=sn[:c]
        for i in range(16):
            hp=base+i*(BEAT//4); h=hat(op=(i%8==7)); e=min(hp+len(h),d); c=e-hp
            if c>0: s[hp:e]+=h[:c]
        for b in rng.choice(16,size=4,replace=False):
            hz=EGYPT_HZ[rng.randint(0,len(EGYPT_HZ))]; bp=base+b*(BEAT//4)
            bl=bloop(hz,BEAT//2); e=min(bp+len(bl),d); c=e-bp
            if c>0: s[bp:e]+=bl[:c]
    return s

if __name__=='__main__':
    master=np.zeros(DUR); seed=np.zeros(BARS_PER*BAR)
    for gen in range(GENS):
        is_fire=(gen%2==0); ps=gen*BARS_PER*BAR; pl=BARS_PER*BAR
        sp=float(np.mean(np.abs(seed)))*10*np.pi
        phrase=grid(BARS_PER,gen)*0.7+arp(gen,sp,BARS_PER)*0.6+fire_layer(pl,is_fire)*0.3+stut(lpf(seed,800)*(0.18+gen*0.02),8,0.25,gen)
        if gen%3==2: phrase=stut(phrase,16,0.2,gen*7)
        phrase=dist(phrase,1.8) if is_fire else rev(phrase,60,0.35)
        pk=np.max(np.abs(phrase)); phrase=phrase/pk*0.85 if pk>0 else phrase
        master[ps:ps+pl]+=phrase; seed=phrase.copy()
        print(f'GEN {gen+1}/8 {"FIRE" if is_fire else "NOFIRE"} peak={pk:.3f}')
    master=lpf(master,18000); pk=np.max(np.abs(master)); master=master/pk*0.92 if pk>0 else master
    r=np.concatenate([np.zeros(441),master[:-441]])
    wavfile.write('/tmp/evez_wheel.wav',SR,(np.stack([master,r],axis=-1)*32767).astype(np.int16))
    print('DONE: /tmp/evez_wheel.wav | 24s stereo 16-bit')

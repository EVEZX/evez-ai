#!/usr/bin/env python3
"""
gen_video_keyframe.py — EVEZ-OS Fast Video Generator (CANONICAL)

Uses matplotlib keyframe savefig + ffmpeg concat demuxer.
Renders 12 keyframes in ~15s. No FuncAnimation overhead.
Output: ~0.3-0.5MB MP4, 1280x720, ~10s.

Usage:
    python gen_video_keyframe.py --state /path/to/hyperloop_state.json --output /tmp/arc.mp4
"""
import json, math, os, subprocess, argparse, time
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.gridspec as gridspec, matplotlib.patches as mpatches

BG='#040408';FG='#dde8f0';DIM='#445566';ACCENT='#ff3a1a'
CEILING_C='#ffd700';COLD_C='#00d4ff';PRIME_C='#cc44ff';GRID_C='#111820';PANEL_EDGE='#1a2535'

def factorize(n):
    f={};d=2
    while d*d<=n:
        while n%d==0:f[d]=f.get(d,0)+1;n//=d
        d+=1
    if n>1:f[n]=f.get(n,0)+1
    return f

def tau_safe(n):
    if n<2:return 1
    t=1
    for e in factorize(n).values():t*=(e+1)
    return t

def omega_k(n):return len(factorize(n))

def build_arc(state):
    GAMMA=0.08;ADM=1.0;cr=state['current_round']
    anchors={int(k[1:-7]):v for k,v in state.items()
             if k.startswith('r') and k.endswith('_result') and isinstance(v,dict)}
    all_rounds=[];V_sim=0.0
    for rn in range(1,cr+1):
        N=rn+51
        if rn in anchors:N=anchors[rn].get('N',N)
        tau=tau_safe(N);ok=omega_k(N);topo=1+0.15*ok
        pc=(topo*(1+math.log(tau))/math.log2(N+1)) if tau>1 else 0.0
        fire=pc>=0.5;V_sim+=GAMMA*ADM*(1+pc);is_prime=ok==1 and tau==2
        if rn in anchors and anchors[rn].get('V_global') is not None:
            v=anchors[rn]['V_global'];pc2=anchors[rn].get('poly_c',pc)
            fire2=anchors[rn].get('fire_ignited',fire);tau2=anchors[rn].get('tau',tau)
        else:v=V_sim;pc2=pc;fire2=fire;tau2=tau
        all_rounds.append({'round':rn,'N':N,'V':v,'poly_c':pc2,'fire':fire2,'tau':tau2,'prime':is_prime})
    return all_rounds

def make_frame(all_rounds,reveal_count,V_v2=6.0):
    fig=plt.figure(figsize=(1280/100,720/100),dpi=100,facecolor=BG)
    gs=gridspec.GridSpec(2,2,figure=fig,left=0.07,right=0.97,top=0.88,bottom=0.08,hspace=0.45,wspace=0.32)
    ax_arc=fig.add_subplot(gs[0,0]);ax_rad=fig.add_subplot(gs[0,1],projection='polar')
    ax_topo=fig.add_subplot(gs[1,0]);ax_tick=fig.add_subplot(gs[1,1])
    for ax in [ax_arc,ax_topo,ax_tick]:ax.set_facecolor(BG)
    ax_rad.set_facecolor(BG);fig.patch.set_facecolor(BG)
    revealed=all_rounds[:reveal_count];cur=revealed[-1];N_total=len(all_rounds)
    fires=sum(1 for r in revealed if r['fire'])
    status='FIRE' if cur['fire'] else('PRIME' if cur['prime'] else 'COOL')
    clr_s=ACCENT if status=='FIRE' else(PRIME_C if status=='PRIME' else COLD_C)
    fig.text(0.5,0.956,'EVEZ-OS  //  FULL ARC PLAYBACK  //  @EVEZ666',ha='center',fontsize=11,color=FG,fontfamily='monospace',fontweight='bold')
    fig.text(0.5,0.933,f'R{cur["round"]}  N={cur["N"]}  tau={cur["tau"]}  pc={cur["poly_c"]:.4f}  [{status}]  V={cur["V"]:.6f}  FIRES:{fires}',ha='center',fontsize=7.5,color=clr_s,fontfamily='monospace')
    def style(ax,t):
        ax.set_facecolor(BG);ax.set_title(t,color=DIM,fontsize=7,loc='left',fontfamily='monospace',pad=3)
        for sp in ax.spines.values():sp.set_color(PANEL_EDGE)
        ax.tick_params(colors=DIM,labelsize=6);ax.grid(True,color=GRID_C,lw=0.4,alpha=0.6)
    all_V=[r['V'] for r in all_rounds]
    y_min=max(0,min(all_V)-0.1);y_max=max(V_v2+0.4,max(all_V)+0.2)
    style(ax_arc,'V_GLOBAL ARC')
    rx=[r['round'] for r in revealed];ry=[r['V'] for r in revealed]
    ax_arc.plot(range(1,N_total+1),all_V,color=DIM,lw=0.3,alpha=0.2,ls=':',zorder=1)
    ax_arc.axhline(V_v2,color=CEILING_C,lw=0.7,ls='--',alpha=0.4)
    if len(rx)>1:
        for i in range(len(rx)-1):
            c=ACCENT if revealed[i]['fire'] else COLD_C;a=0.45+0.55*min(revealed[i]['poly_c']/0.6,1.0)
            ax_arc.plot(rx[i:i+2],ry[i:i+2],color=c,lw=1.2,alpha=a,zorder=3)
    for r in revealed:
        if r['fire']:ax_arc.scatter([r['round']],[r['V']],color=ACCENT,s=60,zorder=6,marker='*')
        elif r['prime']:ax_arc.scatter([r['round']],[r['V']],color=PRIME_C,s=25,zorder=5,marker='D')
    ec=ACCENT if cur['fire'] else(PRIME_C if cur['prime'] else COLD_C)
    ax_arc.scatter([cur['round']],[cur['V']],s=260,color=BG,zorder=7,edgecolors=ec,lw=2)
    ax_arc.scatter([cur['round']],[cur['V']],s=45,color=ec,zorder=8)
    ax_arc.set_xlim(0,N_total+2);ax_arc.set_ylim(y_min,y_max)
    ax_arc.set_xlabel('Round',color=DIM,fontsize=6,fontfamily='monospace');ax_arc.set_ylabel('V_global',color=DIM,fontsize=6,fontfamily='monospace')
    ax_rad.clear();ax_rad.set_facecolor(BG);ax_rad.set_title('POLY_C RADAR',color=DIM,fontsize=7,fontfamily='monospace',pad=6)
    ax_rad.tick_params(colors=DIM,labelsize=5);ax_rad.spines['polar'].set_color(PANEL_EDGE)
    for r in revealed:
        theta=2*math.pi*(r['round']-1)/N_total;pc=min(r['poly_c'],1.2)
        c=ACCENT if r['fire'] else(PRIME_C if r['prime'] else COLD_C);a=0.25+0.75*(r['round']/N_total)
        ax_rad.plot([theta,theta],[0,pc],color=c,lw=0.7,alpha=a)
    theta_ring=np.linspace(0,2*np.pi,200);ax_rad.plot(theta_ring,[0.5]*200,color=CEILING_C,lw=0.7,ls='--',alpha=0.5)
    theta_cur=2*math.pi*(reveal_count-1)/N_total;pc_cur=min(cur['poly_c'],1.2)
    ax_rad.plot([theta_cur,theta_cur],[0,max(pc_cur,0.04)],color=FG,lw=2,alpha=0.9,zorder=10)
    ax_rad.set_ylim(0,1.3);ax_rad.set_xticks([]);ax_rad.set_yticks([0.25,0.5,0.75,1.0])
    ax_rad.yaxis.set_tick_params(labelsize=4,labelcolor=DIM);ax_rad.grid(True,color=GRID_C,alpha=0.4,lw=0.3)
    style(ax_topo,'TOPOLOGY HEATMAP')
    nc=max(1,min(40,reveal_count));nr=math.ceil(reveal_count/nc);cg=np.zeros((nr,nc,4))
    for i,r in enumerate(revealed):
        row=i//nc;col=i%nc;val=min(r['tau']/12.0,1.0)
        if r['fire']:cg[row,col]=[1.0,0.22,0.10,min(0.3+val*0.7,1.0)]
        elif r['prime']:cg[row,col]=[0.8,0.27,1.00,min(0.3+val*0.7,1.0)]
        else:cg[row,col]=[0.0,0.83,1.00,min(0.15+val*0.7,1.0)]
    ax_topo.imshow(cg,aspect='auto',interpolation='nearest',origin='upper',extent=[0,nc,nr,0])
    cr2=(reveal_count-1)//nc;cc2=(reveal_count-1)%nc
    rect=mpatches.Rectangle((cc2,cr2),1,1,fill=False,edgecolor=FG,lw=1.5);ax_topo.add_patch(rect)
    ax_topo.set_xlabel('col',color=DIM,fontsize=6,fontfamily='monospace');ax_topo.set_ylabel('row',color=DIM,fontsize=6,fontfamily='monospace')
    ax_tick.set_facecolor(BG);ax_tick.set_title('OMEGA TICKER',color=DIM,fontsize=7,loc='left',fontfamily='monospace',pad=3);ax_tick.axis('off')
    max_l=16;start=max(0,reveal_count-max_l);vis=revealed[start:]
    for j,r in enumerate(vis):
        y=1.0-(j+1)/(max_l+1);age=len(vis)-1-j;a=max(0.15,1.0-age*0.065)
        c=ACCENT if r['fire'] else(PRIME_C if r['prime'] else COLD_C)
        fw='bold' if j==len(vis)-1 else 'normal';a2=1.0 if j==len(vis)-1 else a
        s='FIRE' if r['fire'] else('PRIME' if r['prime'] else 'COOL')
        ax_tick.text(0.01,y,f"R{r['round']} N={r['N']} tau={r['tau']} pc={r['poly_c']:.3f} [{s}] V={r['V']:.5f}",
                     transform=ax_tick.transAxes,fontsize=6,color=c,alpha=a2,fontfamily='monospace',fontweight=fw,va='center')
    ax_tick.text(0.99,0.02,f'FIRES:{fires}  R{cur["round"]}/{N_total}',transform=ax_tick.transAxes,fontsize=6,color=DIM,ha='right',va='bottom',fontfamily='monospace')
    return fig

def render(state_path,output_path):
    t0=time.time()
    with open(state_path) as f:state=json.load(f)
    all_rounds=build_arc(state);N=len(all_rounds)
    V_v2=state.get('maturity',{}).get('V_v2',6.0)
    kf_counts=[max(1,int(N*p)) for p in[0.13,0.26,0.40,0.53,0.66,0.79,0.89,0.96,0.98,0.99,0.995,1.0]]
    kf_counts[-1]=N;durations=[0.7]*10+[0.6,4.5]
    fd=f'/tmp/evez_kf_{os.getpid()}';os.makedirs(fd,exist_ok=True)
    cf=f'{fd}/concat.txt'
    with open(cf,'w') as fc:
        for i,(rc,dur) in enumerate(zip(kf_counts,durations)):
            fig=make_frame(all_rounds,rc,V_v2);p=f'{fd}/f{i:03d}.png'
            fig.savefig(p,dpi=100,bbox_inches='tight',pad_inches=0,facecolor=BG);plt.close(fig)
            fc.write(f"file '{os.path.abspath(p)}'\nduration {dur}\n")
        fc.write(f"file '{os.path.abspath(f'{fd}/f{len(kf_counts)-1:03d}.png')}'\n")
    cmd=['ffmpeg','-y','-f','concat','-safe','0','-i',cf,
         '-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=#040408,format=yuv420p',
         '-c:v','libx264','-crf','22','-preset','fast','-r','24','-movflags','+faststart',output_path]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    if r.returncode!=0:raise RuntimeError(r.stderr[-500:])
    size_mb=os.path.getsize(output_path)/1e6
    print(f"RENDERED: {output_path}  {size_mb:.2f}MB  {time.time()-t0:.1f}s  {N} rounds")

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--state',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    render(args.state,args.output)

#!/usr/bin/env python3
"""
EVEZ-OS Max Visual Density — 5-Panel Cinematic Speed Run
Usage: python gen_video_speedrun.py --state <state_json_path> --output /tmp/out.mp4 --tail 25 --fps 30
Fetches arc from GitHub raw if state is stale.
"""
import math, numpy as np, os, sys, json, urllib.request, argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')

GITHUB_STATE = "https://raw.githubusercontent.com/EvezArt/evez-os/main/hyperloop_state.json"

# Canonical arc (R96-R120) — extended on each run from state
CANONICAL_ARC = [
    (96,48,"48=2⁴×3",3,1.30,0.382,False,"",1.702003,14,""),
    (97,49,"49=7²",2,1.15,0.310,False,"",1.731003,15,""),
    (98,50,"50=2×5²",3,1.30,0.378,False,"",1.760003,16,""),
    (99,51,"51=3×17",2,1.30,0.374,False,"",1.789003,17,""),
    (100,52,"52=2²×13",3,1.30,0.375,False,"",1.818003,18,""),
    (101,53,"53=PRIME",1,1.15,0.000,False,"",1.898003,19,"PRIME"),
    (102,54,"54=2×3³",4,1.30,0.500,True,"SEVENTH",1.940003,20,"SEVENTH"),
    (103,55,"55=5×11",2,1.15,0.408,False,"",1.995003,21,"COOL"),
    (104,56,"56=2³×7",3,1.30,0.505,True,"EIGHTH",2.020003,22,"EIGHTH"),
    (105,57,"57=3×19",2,1.30,0.406,False,"",2.045003,23,"COOL"),
    (106,58,"58=2×29",2,1.30,0.405,False,"",2.070003,24,""),
    (107,59,"59=PRIME",1,1.15,0.000,False,"",2.150003,25,"PRIME"),
    (108,60,"60=2²×3×5",3,1.45,0.499,False,"",2.170003,26,"NEAR"),
    (109,61,"61=PRIME",1,1.15,0.000,False,"",2.170003,27,"PRIME"),
    (110,62,"62=2×31",2,1.30,0.400,False,"",2.170003,28,""),
    (111,63,"63=3²×7",3,1.30,0.495,False,"",2.195003,29,"NEAR3"),
    (112,64,"64=2⁶",7,1.15,0.693,True,"TENTH",2.220003,30,"TENTH"),
    (113,65,"65=5×13",2,1.30,0.397,False,"",2.245003,31,"COOL"),
    (114,66,"66=2×3×11",4,1.45,0.570,True,"ELEVENTH",2.370635,32,"ELEVENTH"),
    (115,67,"67=PRIME",1,1.15,0.000,False,"",2.450635,33,"PRIME"),
    (116,68,"68=2²×17",2,1.30,0.351,False,"",2.559294,34,""),
    (117,69,"69=3×23",2,1.30,0.361,False,"",2.668042,35,""),
    (118,70,"70=2×5×7",3,1.45,0.495,False,"",2.787637,36,"NEAR"),
    (119,71,"71=PRIME",1,1.15,0.000,False,"",2.867637,37,"PRIME"),
    (120,72,"72=2³×3²",4,1.30,0.501,True,"TWELFTH",2.987731,38,"TWELFTH"),
]

BG='#030306'; FIRE_C='#ff2200'; NEAR_C='#ff8800'; PRIME_C='#cc44ff'
OK_C='#00ff88'; VAL_C='#ffaa00'; CEIL_C='#ff4400'; GRID_C='#0d0d18'
TEXT_C='#dde0e8'

def pt_color(fire, poly_c, label):
    if fire: return FIRE_C
    if poly_c >= 0.45: return NEAR_C
    if 'PRIME' in label: return PRIME_C
    return OK_C

def render(arc, output, fps=30, hold_s=2.5):
    rounds=[a[0] for a in arc]; Vgs=[a[8] for a in arc]
    fires=[a[6] for a in arc]; poly_cs=[a[5] for a in arc]
    taus=[a[3] for a in arc]; labels=[a[10] for a in arc]
    fire_names=[a[7] for a in arc]

    build_frames=fps//4
    total_anim=len(arc)*build_frames
    hold_frames=int(hold_s*fps)
    total_frames=total_anim+hold_frames

    fig=plt.figure(figsize=(16,9),facecolor=BG,dpi=90)
    gs=GridSpec(3,3,figure=fig,hspace=0.38,wspace=0.32,left=0.06,right=0.98,top=0.93,bottom=0.07)
    ax_main=fig.add_subplot(gs[0:2,0:2])
    ax_poly=fig.add_subplot(gs[2,0:2])
    ax_tau=fig.add_subplot(gs[0,2])
    ax_info=fig.add_subplot(gs[1,2])
    ax_fire=fig.add_subplot(gs[2,2])

    for ax in [ax_main,ax_poly,ax_tau,ax_info,ax_fire]:
        ax.set_facecolor(BG)
        ax.tick_params(colors='#333355',labelsize=6.5)
        for sp in ax.spines.values(): sp.set_color(GRID_C)

    ax_main.set_xlim(rounds[0]-0.5,rounds[-1]+0.5)
    ax_main.set_ylim(min(Vgs)-0.05,max(Vgs)+0.18)
    ax_main.set_xlabel("Round",color='#444466',fontsize=8)
    ax_main.set_ylabel("V_global",color='#444466',fontsize=8)
    ax_main.set_title(f"EVEZ-OS // ARC R{rounds[0]}-R{rounds[-1]}",color=CEIL_C,fontsize=12,fontweight='bold',pad=6)
    ax_main.axhline(y=3.0,color=CEIL_C,lw=0.5,ls='--',alpha=0.3)
    ax_main.grid(axis='y',color=GRID_C,lw=0.3,alpha=0.5)

    line_main,=ax_main.plot([],[],color='#2244cc',lw=1.5,alpha=0.8,zorder=3)
    scat_main=ax_main.scatter([],[],s=55,zorder=5)

    ax_poly.set_xlim(rounds[0]-0.5,rounds[-1]+0.5)
    ax_poly.set_ylim(0,max(poly_cs)+0.12)
    ax_poly.axhline(y=0.500,color=FIRE_C,lw=0.8,ls='--',alpha=0.6)
    ax_poly.set_ylabel("poly_c",color='#444466',fontsize=7)
    ax_poly.grid(axis='y',color=GRID_C,lw=0.2,alpha=0.4)
    bc=[FIRE_C if f else (NEAR_C if p>=0.45 else (PRIME_C if p==0 else '#1a1a2e'))
        for f,p in zip(fires,poly_cs)]
    poly_bars=ax_poly.bar(rounds,[0]*len(rounds),width=0.7,color=bc,alpha=0.0)

    ax_tau.set_xlim(rounds[0]-0.5,rounds[-1]+0.5)
    ax_tau.set_ylim(0,1); ax_tau.set_yticks([])
    ax_tau.set_title("tau",color='#444466',fontsize=7.5,pad=3)
    tau_cmap=LinearSegmentedColormap.from_list('tau',['#050510','#0022aa','#ff8800','#ff2200'])
    tau_norm=plt.Normalize(vmin=1,vmax=8)
    tau_rects=[]
    for r,t in zip(rounds,taus):
        rect=mpatches.FancyBboxPatch((r-0.4,0.1),0.8,0.8,
            boxstyle="round,pad=0.05",facecolor=tau_cmap(tau_norm(t)),alpha=0.0,edgecolor='none')
        ax_tau.add_patch(rect); tau_rects.append(rect)

    ax_info.set_xlim(0,1); ax_info.set_ylim(0,1)
    ax_info.set_xticks([]); ax_info.set_yticks([])
    ax_info.set_title("LIVE STATE",color='#444466',fontsize=7.5,pad=3)
    info_texts={}
    for i,(k,lbl) in enumerate(zip(['R','N','tau','poly_c','V','ceil','status'],['Round','N','tau','poly_c','V_global','CEIL','STATUS'])):
        y=0.88-i*0.12
        ax_info.text(0.05,y,lbl+':',color='#333355',fontsize=7.5,va='top')
        t=ax_info.text(0.55,y,'—',color=VAL_C,fontsize=7.5,va='top',fontweight='bold')
        info_texts[k]=t
    eq_text=ax_info.text(0.05,0.02,'',color='#1a1a3a',fontsize=5.8,va='bottom')

    fire_count_seen=[0]; last_fire_f=[-999]
    ax_fire.set_xlim(0,1); ax_fire.set_ylim(0,1)
    ax_fire.set_xticks([]); ax_fire.set_yticks([])
    ax_fire.set_title("FIRES",color='#444466',fontsize=7.5,pad=3)
    fct=ax_fire.text(0.5,0.7,'0',color=FIRE_C,fontsize=32,fontweight='bold',ha='center',va='center',alpha=0.0)
    fnm=ax_fire.text(0.5,0.25,'',color=FIRE_C,fontsize=9,fontweight='bold',ha='center')
    fvg=ax_fire.text(0.5,0.1,'',color=VAL_C,fontsize=7,ha='center')

    fig.text(0.5,0.975,f'EVEZ-OS SPEED RUN  //  R{rounds[0]}-R{rounds[-1]}  //  12 FIRES  //  ◊ CANONICAL',
        color=CEIL_C,fontsize=8,ha='center',va='top',fontweight='bold')

    def anim(frame):
        n=min(frame//build_frames+1,len(arc)) if frame<total_anim else len(arc)
        vr=rounds[:n]; vV=Vgs[:n]; vf=fires[:n]; vp=poly_cs[:n]
        line_main.set_data(vr,vV)
        colors=[pt_color(fires[i],poly_cs[i],labels[i]) for i in range(n)]
        scat_main.set_offsets(list(zip(vr,vV))); scat_main.set_color(colors)
        cur_fires=sum(vf)
        if cur_fires>fire_count_seen[0]:
            for i in range(n-1,-1,-1):
                if vf[i] and i>=fire_count_seen[0]:
                    ax_main.annotate(fire_names[i],xy=(vr[i],vV[i]),
                        xytext=(vr[i]+0.2,vV[i]+0.03),color=FIRE_C,fontsize=5,fontweight='bold',
                        arrowprops=dict(arrowstyle='->',color=FIRE_C,lw=0.4),annotation_clip=True)
            fire_count_seen[0]=cur_fires; last_fire_f[0]=frame
        for i,bar in enumerate(poly_bars):
            if i<n: bar.set_height(vp[i]); bar.set_alpha(0.85)
        for i,rect in enumerate(tau_rects):
            if i<n: rect.set_alpha(0.9)
        last=n-1; a=arc[last]
        sc=a[7] if a[6] else ('NEAR' if 'NEAR' in a[10] else ('PRIME' if 'PRIME' in a[10] else 'NO FIRE'))
        info_texts['R'].set_text(f'R{a[0]}')
        info_texts['N'].set_text(str(a[2]))
        info_texts['tau'].set_text(str(a[3]))
        info_texts['poly_c'].set_text(f'{a[5]:.6f}')
        info_texts['V'].set_text(f'{a[8]:.6f}')
        info_texts['ceil'].set_text(f'x{a[9]}')
        info_texts['status'].set_text(sc)
        info_texts['status'].set_color(FIRE_C if a[6] else (NEAR_C if 'NEAR' in a[10] else (PRIME_C if 'PRIME' in a[10] else OK_C)))
        fct.set_text(str(cur_fires)); fct.set_alpha(min(0.2+cur_fires*0.07,1.0))
        if a[6]: fnm.set_text(a[7]+' FIRE'); fvg.set_text(f'V={a[8]:.6f}')
        return []

    ani=animation.FuncAnimation(fig,anim,frames=total_frames,interval=1000/fps,blit=False)
    w=animation.FFMpegWriter(fps=fps,bitrate=2400,extra_args=['-vcodec','libx264','-pix_fmt','yuv420p','-crf','20','-preset','fast'])
    ani.save(output,writer=w)
    plt.close()
    return os.path.getsize(output)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="/tmp/evez_speedrun.mp4")
    parser.add_argument("--tail",type=int,default=25)
    parser.add_argument("--fps",type=int,default=30)
    args=parser.parse_args()
    arc=CANONICAL_ARC[-args.tail:]
    sz=render(arc,args.output,args.fps)
    print(f"Rendered: {args.output} ({sz:,} bytes)")
    sys.exit(0)

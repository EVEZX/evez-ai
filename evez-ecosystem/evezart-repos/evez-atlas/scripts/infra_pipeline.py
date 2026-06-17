#!/usr/bin/env python3
"""
EVEZ-OS Infrastructure Pipeline
Per-tick: image gen → caption → Ably publish → Backendless upsert

BLOCKERS:
  A) AI/ML API image+vision: verify at aimlapi.com/app/verification
  B) Ably: provide API key in workspace/ably_config.json {"api_key": "xxxxx.yyyyy:zzzzz"}
  C) Backendless: provide keys in workspace/backendless_config.json {"app_id": "", "api_key": ""}

WORKING NOW:
  - Local matplotlib image gen (PLASMA/OBSIDIAN/ICE) ✅
  - S3 upload ✅
  - Rule-based caption fallback ✅
"""
import json, math, os, time
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import concurrent.futures

CONFIG_PATH = "/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/workspace"

def get_palette(rd):
    if rd.get('fire_ignited'): return 'PLASMA'
    elif rd.get('poly_c',0) >= 0.45: return 'OBSIDIAN'
    else: return 'ICE'

def generate_fire_state_image(rd, out_path):
    palette = get_palette(rd)
    R=rd['round']; poly_c=rd.get('poly_c',0); V=rd.get('V_global',0); ceil=rd.get('ceiling_tick',0)
    fig,ax = plt.subplots(1,1,figsize=(16,9),facecolor='#020204')
    ax.set_facecolor('#020204'); ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    np.random.seed(R)
    if palette == 'PLASMA':
        for i in range(60):
            x0=np.random.uniform(0.1,0.9); y0=np.random.uniform(0.0,0.7)
            ax.plot([x0,x0+np.random.uniform(-0.1,0.1)],[y0,y0+np.random.uniform(0.1,0.6)],
                    color=np.random.choice(['#ff2200','#ff5500','#ff8800','#ffaa00']),
                    lw=np.random.uniform(0.5,4), alpha=np.random.uniform(0.3,0.9))
        core_c='#ff2200'
    elif palette == 'OBSIDIAN':
        for i in range(35):
            x0,y0=np.random.uniform(0.1,0.9),np.random.uniform(0.1,0.9)
            ang=np.random.uniform(0,2*np.pi); L=np.random.uniform(0.05,0.35)
            lw=np.random.uniform(0.5,3.5); ag=np.random.uniform(0.2,0.7)
            ax.plot([x0,x0+np.cos(ang)*L],[y0,y0+np.sin(ang)*L],color='#ff4400',lw=lw+3,alpha=ag*0.4)
            ax.plot([x0,x0+np.cos(ang)*L],[y0,y0+np.sin(ang)*L],color='#110a04',lw=lw,alpha=0.95)
        theta=np.linspace(0,2*np.pi*poly_c/0.5,200)
        ax.plot(0.5+0.30*np.cos(theta),0.5+0.30*np.sin(theta),color='#ff6600',lw=2.5,alpha=0.85)
        core_c='#ff4400'
    else:
        for i in range(50):
            x0,y0=np.random.uniform(0,1),np.random.uniform(0,1)
            for j in range(np.random.randint(2,6)):
                ang=j*np.pi/3+np.random.uniform(-0.2,0.2); L=np.random.uniform(0.03,0.18)
                ax.plot([x0,x0+np.cos(ang)*L],[y0,y0+np.sin(ang)*L],
                        color=np.random.choice(['#2244cc','#4466ff','#8899ff']),
                        lw=np.random.uniform(0.3,1.5),alpha=np.random.uniform(0.2,0.8))
        core_c='#4466ff'
    ax.add_patch(plt.Circle((0.5,0.5),0.07,facecolor='#080808',edgecolor=core_c,linewidth=1.5,alpha=0.9))
    ax.text(0.5,0.5,palette,color=core_c,fontsize=8,fontweight='bold',ha='center',va='center',family='monospace',alpha=0.9)
    ax.text(0.03,0.97,f'R{R}',color='#ffffff',fontsize=30,fontweight='bold',va='top',family='monospace')
    ax.text(0.03,0.84,f"N={rd['N_str']}  tau={rd.get('tau',1)}",color='#cc9966',fontsize=13,va='top',family='monospace')
    ax.text(0.03,0.75,f'poly_c = {poly_c:.6f}',color='#ff8800',fontsize=12,va='top',family='monospace')
    ax.text(0.03,0.66,palette,color=core_c,fontsize=15,fontweight='bold',va='top',family='monospace')
    ax.text(0.03,0.07,f'V_global = {V:.6f}  CEILING x{ceil}',color='#aaaacc',fontsize=11,va='bottom',family='monospace')
    plt.savefig(out_path,dpi=140,bbox_inches='tight',facecolor='#020204',format='png')
    plt.close()
    return out_path

def get_caption(rd):
    pc=rd.get('poly_c',0)
    if rd.get('fire_ignited'):
        return f"{rd.get('fire_name','')} FIRE. formula erupts. N={rd['N_str']} poly_c={pc:.3f} crosses threshold."
    elif pc >= 0.48: return f"obsidian razor edge. delta{round(0.5-pc,4)} from ignition. the crack runs deep."
    elif pc >= 0.45: return f"volcanic glass. delta{round(0.5-pc,4)} from fire. threshold energy barely held."
    elif rd.get('tau',1)==1: return "prime silence. tau=1 kills the formula. ice geometry holds."
    else: return f"crystalline climb. poly_c={pc:.3f}. the arc does not stop."

def run_pipeline_tick(rd, tweet_eq_url, upload_fn=None):
    ably_cfg={}; bl_cfg={}
    try: ably_cfg=json.load(open(f"{CONFIG_PATH}/ably_config.json"))
    except: pass
    try: bl_cfg=json.load(open(f"{CONFIG_PATH}/backendless_config.json"))
    except: pass
    R=rd['round']; out_path=f"/tmp/evez_r{R}_artwork.png"
    generate_fire_state_image(rd, out_path)
    image_url=""
    if upload_fn:
        r,e=upload_fn(out_path)
        if not e: image_url=r.get('s3_url','')
    caption=get_caption(rd)
    payload={**rd,'tweet_url':tweet_eq_url,'image_url':image_url,'caption':caption,'ts':int(time.time())}
    results={'image_url':image_url,'caption':caption,'ably_ok':False,'backendless_ok':False}
    def try_ably():
        if not ably_cfg.get('api_key'): return False,'NO_KEY'
        import requests; key=ably_cfg['api_key']
        r=requests.post('https://rest.ably.io/channels/evez:round/messages',
            auth=(key.split(':')[0],key.split(':')[1]),
            json={'name':'round:complete','data':payload})
        return r.status_code==201,str(r.status_code)
    def try_bl():
        if not bl_cfg.get('app_id'): return False,'NO_KEY'
        import requests
        r=requests.post(f"https://api.backendless.com/{bl_cfg['app_id']}/{bl_cfg['api_key']}/data/evez_rounds",
            json={**payload,'fire_state':'FIRE' if rd.get('fire_ignited') else ('NEAR_MISS' if rd.get('poly_c',0)>=0.45 else 'NO_FIRE')},
            headers={'Content-Type':'application/json'})
        return r.status_code in(200,201),str(r.status_code)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        af=ex.submit(try_ably); bf=ex.submit(try_bl)
        ok_a,msg_a=af.result(); ok_b,msg_b=bf.result()
        results['ably_ok']=ok_a; results['ably_msg']=msg_a
        results['backendless_ok']=ok_b; results['backendless_msg']=msg_b
    return results

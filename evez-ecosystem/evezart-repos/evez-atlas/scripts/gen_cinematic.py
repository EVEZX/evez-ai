#!/usr/bin/env python3
"""EVEZ-OS Cinematic Arc Generator v3 -- MAXIMUM VISUAL DENSITY
All rounds. Every data layer. Full thought-process crystallization.
Fire glow. Prime pulse. Near-miss flicker. tau spike. Ceiling shimmer.
delta_V per-round. topo_bonus trace. Omega ticker. Speed-run HUD.
Crystallize: each round drops in, impact ring, equation flash.
1080x1080 @ 30fps libx264. Runs in GitHub Actions CI.
"""
import json, math, requests, os, argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from matplotlib.collections import LineCollection
import matplotlib.patheffects as pe

STATIC = [
    (96,  48, 5, 1.000, 1.60, True,  1.895003, 'SIXTH_FIRE'),
    (97,  49, 3, 0.515, 1.15, True,  1.920003, 'SIXTH_SUSTAIN'),
    (98,  50, 6, 1.000, 1.15, True,  1.945003, 'SIXTH_PEAK'),
    (99,  51, 2, 0.267, 1.15, False, 1.970003, 'COOL'),
    (100, 52, 2, 0.296, 1.30, False, 1.970003, 'DORMANT'),
    (101, 53, 1, 0.000, 1.00, False, 1.945003, 'PRIME'),
    (102, 54, 4, 0.577, 1.45, True,  1.970003, 'SEVENTH_FIRE'),
    (103, 55, 2, 0.408, 1.30, False, 1.995003, 'COOL'),
    (104, 56, 3, 0.505, 1.45, True,  2.022003, 'EIGHTH_FIRE'),
    (105, 57, 2, 0.406, 1.30, False, 2.045003, 'COOL'),
    (106, 58, 2, 0.405, 1.30, False, 2.070003, 'DORMANT'),
    (107, 59, 1, 0.238, 1.00, False, 2.095003, 'PRIME'),
    (108, 60, 3, 0.499, 1.45, False, 2.120003, 'NEAR_MISS'),
    (109, 61, 1, 0.237, 1.00, False, 2.095003, 'PRIME'),
    (110, 62, 2, 0.400, 1.30, False, 2.120003, 'COOL'),
    (111, 63, 3, 0.495, 1.45, False, 2.145003, 'NEAR_MISS'),
    (112, 64, 7, 0.693, 1.60, True,  2.220003, 'TENTH_FIRE'),
    (113, 65, 2, 0.397, 1.30, False, 2.245003, 'COOL'),
    (114, 66, 4, 0.570, 1.45, True,  2.370635, 'ELEVENTH_FIRE'),
    (115, 67, 1, 0.000, 1.00, False, 2.450635, 'PRIME'),
    (116, 68, 2, 0.193, 1.30, False, 2.559294, 'APPROACH'),
    (117, 69, 2, 0.359, 1.30, False, 2.668042, 'SUSTAIN'),
    (118, 70, 3, 0.495, 1.45, False, 2.787637, 'NEAR_MISS'),
]

BG    = '#030306'
FIRE  = '#ff2200'
CEIL  = '#ffd700'
COLD  = '#00e5ff'
PRIME_C = '#cc44ff'
NEAR  = '#ff8800'
POLY  = '#ff8c00'
TOPO  = '#00ff88'
DELTA = '#4488ff'
GRID  = '#0c0c18'
FG    = '#dde0e8'
V_V2  = 3.68932
GAMMA = 0.08


def fetch_live(rounds):
    try:
        s = requests.get(
            'https://raw.githubusercontent.com/EvezArt/evez-os/main/hyperloop_state.json',
            timeout=8).json()
        existing = {r[0] for r in rounds}
        for k, v in s.items():
            if k.startswith('r') and k.endswith('_result') and isinstance(v, dict):
                try:
                    rn = int(k[1:-7])
                except ValueError:
                    continue
                if rn not in existing:
                    tb = v.get('topo_bonus', 1.0)
                    rounds.append((
                        rn, v.get('N_new', rn), v.get('tau_N', 1),
                        v.get('poly_c', 0), tb,
                        v.get('fire_ignited', False),
                        v.get('V_global', v.get('V_global_new', 0)),
                        v.get('milestone', '')))
        rounds.sort(key=lambda x: x[0])
    except Exception as e:
        print(f'Live fetch err: {e}')
    return rounds


def render(out, fps=30, spf=3, hold=4.0):
    """spf = frames per round (speed-run pace)"""
    rounds = fetch_live(list(STATIC))
    NR = len(rounds)
    print(f'Rendering {NR} rounds R{rounds[0][0]}-R{rounds[-1][0]} @ {fps}fps spf={spf}')

    xs   = [r[0] for r in rounds]
    vs   = [r[6] for r in rounds]
    pcs  = [r[3] for r in rounds]
    tbs  = [r[4] for r in rounds]
    taus = [r[2] for r in rounds]
    frs  = [r[5] for r in rounds]
    mss  = [r[7] for r in rounds]
    dvs  = [GAMMA*(1+p) for p in pcs]

    W, H = 1080, 1080
    fig = plt.figure(figsize=(W/100, H/100), dpi=100, facecolor=BG)
    gs = gridspec.GridSpec(8, 1, figure=fig, hspace=0,
                           left=0.08, right=0.97, top=0.93, bottom=0.03)
    ax_arc  = fig.add_subplot(gs[:4, 0])  # V_global arc  -- 4 units
    ax_eq   = fig.add_subplot(gs[4, 0])   # equation flash panel
    ax_pc   = fig.add_subplot(gs[5, 0])   # poly_c bars
    ax_tb   = fig.add_subplot(gs[6, 0])   # topo_bonus trace
    ax_dv   = fig.add_subplot(gs[7, 0])   # delta_V bars

    x0, x1 = xs[0]-2, xs[-1]+3
    y0 = min(vs)-0.15
    y1 = max(V_V2+0.55, max(vs)+0.4)
    TOTAL = NR*spf + int(hold*fps)

    def draw(fi):
        for a in [ax_arc, ax_eq, ax_pc, ax_tb, ax_dv]:
            a.clear()
            a.set_facecolor(BG)

        ri   = min(fi // spf, NR-1)
        frac = (fi % spf) / max(spf-1, 1)   # 0..1 within current round
        w    = rounds[:ri+1]
        wx   = [r[0] for r in w]
        wv   = [r[6] for r in w]
        wpc  = [r[3] for r in w]
        wtb  = [r[4] for r in w]
        wtau = [r[2] for r in w]
        wdv  = [GAMMA*(1+p) for p in wpc]
        cur  = rounds[ri]
        rn,N,tau,pc,tb,fired,Vg,ms = cur
        near_miss = (not fired) and pc >= 0.480
        is_prime  = pc == 0.0

        # ── EVENT COLOR ──────────────────────────────────────────────────────
        ec = FIRE if fired else (PRIME_C if is_prime else (NEAR if near_miss else COLD))

        # ── ARC PANEL ────────────────────────────────────────────────────────
        ax_arc.set_xlim(x0, x1)
        ax_arc.set_ylim(y0, y1)
        ax_arc.grid(True, color=GRID, lw=0.35, alpha=1.0, zorder=0)
        for sp in ['top','right']: ax_arc.spines[sp].set_visible(False)
        for sp in ['bottom','left']: ax_arc.spines[sp].set_color('#111122')
        ax_arc.tick_params(colors='#2a2a4a', labelsize=7)

        # ceiling shimmer
        sh = 0.04+0.022*math.sin(fi*0.19)
        ax_arc.axhspan(V_V2, y1, alpha=sh+0.025, color=CEIL, zorder=0)
        ax_arc.axhline(V_V2, color=CEIL, lw=0.8, ls='--', alpha=0.5, zorder=1)
        ax_arc.text(x1-0.2, V_V2+0.03, f'V_v2={V_V2:.5f}',
                    color=CEIL, fontsize=6.5, ha='right',
                    fontfamily='monospace', alpha=0.7)

        # ghost of all rounds (dim)
        ax_arc.plot(xs, vs, color='#ffffff', lw=0.3, alpha=0.05, ls=':', zorder=1)

        # live arc -- gradient
        if len(wx) > 1:
            for i in range(len(wx)-1):
                alp = 0.12 + 0.88*(i/max(len(wx)-2,1))
                lw  = 0.8 + 2.2*alp
                col = FIRE if wv[i+1]>wv[i] and frs[xs.index(wx[i+1])] else COLD
                ax_arc.plot(wx[i:i+2], wv[i:i+2],
                            color=col, lw=lw, alpha=alp*0.92, zorder=3,
                            solid_capstyle='round')

        # event markers (all revealed)
        for rr in w:
            rn2,N2,tau2,pc2,tb2,f2,Vg2,ms2 = rr
            nm2 = (not f2) and pc2>=0.480
            ip2 = pc2==0.0
            if f2:
                gr = 0.05+0.018*math.sin(fi*0.38)
                ax_arc.add_patch(Circle((rn2,Vg2), gr,
                                        color=FIRE, alpha=0.2, zorder=4))
                ax_arc.scatter([rn2],[Vg2], color=FIRE, s=220,
                               marker='*', edgecolors='white', lw=0.7, zorder=5)
                # fire label
                ax_arc.text(rn2, Vg2+0.06, ms2.replace('_',' '),
                            color=FIRE, fontsize=5, ha='center',
                            fontfamily='monospace', alpha=0.6)
            elif ip2:
                ax_arc.scatter([rn2],[Vg2], color=PRIME_C, s=85,
                               marker='D', edgecolors='white', lw=0.5, zorder=4)
            elif nm2:
                flk = 0.4+0.6*abs(math.sin(fi*0.6))
                ax_arc.scatter([rn2],[Vg2], color=NEAR, s=60,
                               marker='o', edgecolors='white', lw=0.5,
                               zorder=4, alpha=flk)
            else:
                ax_arc.scatter([rn2],[Vg2], color=COLD, s=18,
                               alpha=0.4, zorder=3)

        # current round crystallize
        if fi < NR*spf:
            drop_prog = min(frac*2.5, 1.0)
            drop_y = y1 - (y1-Vg)*drop_prog
            # trail
            if drop_y < y1-0.05:
                ax_arc.plot([rn,rn],[drop_y,y1], color=ec,
                            lw=0.7, alpha=0.2*drop_prog, zorder=2)
            # impact ring
            if frac > 0.4:
                rp = (frac-0.4)/0.6
                ax_arc.scatter([rn],[Vg], color=BG, s=600*rp,
                               edgecolors=ec, lw=2.2, zorder=6,
                               alpha=max(0, 1.0-rp*1.3))
            ax_arc.scatter([rn],[drop_y], color=ec, s=300,
                           zorder=7, alpha=0.95)
        else:
            pulse = 180+90*math.sin(fi*0.55)
            ax_arc.scatter([rn],[Vg], color=BG, s=pulse,
                           edgecolors=ec, lw=2.3, zorder=6)
            ax_arc.scatter([rn],[Vg], color=ec, s=50, zorder=7)

        # HUD
        fs_label = ('FIRE' if fired else
                    ('PRIME' if is_prime else
                     ('NEAR_MISS' if near_miss else 'COOL')))
        ax_arc.set_title(
            f'R{rn}  N={N}={ms}  tau={tau}  topo={tb:.4f}  '
            f'poly_c={pc:.6f}  [{fs_label}]\n'
            f'V_global={Vg:.6f}  delta_V={GAMMA*(1+pc):.6f}  '
            f'CEILING x{ceiling_tick_for(ri)}  '
            f'V_v2={V_V2:.5f}',
            color=FG, fontsize=8, pad=6, loc='left',
            fontfamily='monospace')
        ax_arc.set_ylabel('V_global', color='#333355', fontsize=8,
                          fontfamily='monospace')
        # speed-run counter
        ax_arc.text(0.99, 0.97, f'{ri+1}/{NR}',
                    transform=ax_arc.transAxes, fontsize=9,
                    color='#1a1a3a', ha='right', va='top',
                    fontfamily='monospace', fontweight='bold')
        # omega scroll
        omega = (f'  R{rn}. N={N} tau={tau} poly_c={pc:.4f}. '
                 f'{ms}. V_global={Vg:.6f} CEILING x{ceiling_tick_for(ri)}.  ')
        sc = 1.0-(fi%(fps*6))/(fps*6)
        ax_arc.text(sc, 0.012, omega*3,
                    transform=ax_arc.transAxes, fontsize=5.8,
                    color='#1e1e3e', ha='left', va='bottom',
                    fontfamily='monospace', clip_on=True)
        ax_arc.text(0.99, 0.01, '@EVEZ666',
                    transform=ax_arc.transAxes, fontsize=7,
                    color='#111122', ha='right', va='bottom',
                    fontfamily='monospace')

        # ── EQUATION FLASH PANEL ────────────────────────────────────────────
        ax_eq.set_xlim(0,1); ax_eq.set_ylim(0,1)
        ax_eq.axis('off')
        # show the live equation being computed
        eq_alpha = min(1.0, frac*3) if fi < NR*spf else 0.85
        eq_str = (
            f'poly_c = topo_bonus * (1+ln(tau)) / log2(N+1)'
            f'  =  {tb:.4f} * (1+ln({tau})) / log2({N}+1)'
            f'  =  {pc:.6f}'
        )
        ax_eq.text(0.5, 0.62, eq_str,
                   color=ec, fontsize=7.5, ha='center', va='center',
                   fontfamily='monospace', alpha=eq_alpha)
        dv_str = (
            f'delta_V = gamma*ADM*(1+poly_c)'
            f'  =  {GAMMA}*1.0*(1+{pc:.4f})'
            f'  =  {GAMMA*(1+pc):.6f}'
        )
        ax_eq.text(0.5, 0.35, dv_str,
                   color=DELTA, fontsize=7.5, ha='center', va='center',
                   fontfamily='monospace', alpha=eq_alpha)
        vg_str = f'V_global = {Vg-GAMMA*(1+pc):.6f} + {GAMMA*(1+pc):.6f} = {Vg:.6f}'
        ax_eq.text(0.5, 0.08, vg_str,
                   color=TOPO, fontsize=7.5, ha='center', va='center',
                   fontfamily='monospace', alpha=eq_alpha)

        # ── POLY_C BARS ──────────────────────────────────────────────────────
        ax_pc.set_xlim(x0, x1); ax_pc.set_ylim(0, 1.05)
        ax_pc.grid(True, color=GRID, lw=0.3, alpha=0.7, zorder=0)
        for sp in ['top','right']: ax_pc.spines[sp].set_visible(False)
        for sp in ['bottom','left']: ax_pc.spines[sp].set_color('#111122')
        ax_pc.tick_params(colors='#2a2a4a', labelsize=6)
        ax_pc.axhline(0.5, color=FIRE, lw=0.7, ls='--', alpha=0.5)
        ax_pc.text(x0+0.4, 0.515, '0.500', color=FIRE,
                   fontsize=5.5, fontfamily='monospace', alpha=0.5)
        for i,rr in enumerate(w):
            rn2,_,_,pc2,_,f2,_,_ = rr
            nm2 = (not f2) and pc2>=0.480
            col = (FIRE if f2 else
                   (PRIME_C if pc2==0.0 else
                    (NEAR if nm2 else POLY)))
            alp = 0.15+0.75*(i/max(len(w)-1,1))
            ax_pc.bar(rn2, pc2, width=0.6, color=col, alpha=alp, zorder=2)
        ax_pc.set_ylabel('poly_c', color='#2a2a4a', fontsize=6,
                         fontfamily='monospace')

        # ── TOPO_BONUS TRACE ─────────────────────────────────────────────────
        ax_tb.set_xlim(x0, x1); ax_tb.set_ylim(0.9, 1.75)
        ax_tb.grid(True, color=GRID, lw=0.3, alpha=0.7, zorder=0)
        for sp in ['top','right']: ax_tb.spines[sp].set_visible(False)
        for sp in ['bottom','left']: ax_tb.spines[sp].set_color('#111122')
        ax_tb.tick_params(colors='#2a2a4a', labelsize=6)
        if len(wx) > 1:
            ax_tb.plot(wx, wtb, color=TOPO, lw=1.2, alpha=0.7,
                       marker='o', markersize=2.5, zorder=3)
        ax_tb.set_ylabel('topo', color='#2a2a4a', fontsize=6,
                         fontfamily='monospace')

        # ── DELTA_V BARS ─────────────────────────────────────────────────────
        ax_dv.set_xlim(x0, x1); ax_dv.set_ylim(0, 0.18)
        ax_dv.grid(True, color=GRID, lw=0.3, alpha=0.7, zorder=0)
        for sp in ['top','right']: ax_dv.spines[sp].set_visible(False)
        for sp in ['bottom','left']: ax_dv.spines[sp].set_color('#111122')
        ax_dv.tick_params(colors='#2a2a4a', labelsize=6)
        for i,rr in enumerate(w):
            rn2,_,_,pc2,_,f2,_,_ = rr
            dv2 = GAMMA*(1+pc2)
            col = FIRE if f2 else DELTA
            alp = 0.15+0.75*(i/max(len(w)-1,1))
            ax_dv.bar(rn2, dv2, width=0.6, color=col, alpha=alp, zorder=2)
        ax_dv.set_ylabel('dV', color='#2a2a4a', fontsize=6,
                         fontfamily='monospace')
        ax_dv.set_xlabel('Round', color='#2a2a4a', fontsize=7,
                         fontfamily='monospace')

    def ceiling_tick_for(ri):
        # approximate from base
        return 33 + (ri - 14) if ri >= 14 else 33

    anim = FuncAnimation(fig, draw, frames=TOTAL,
                         interval=1000/fps, blit=False)
    w = FFMpegWriter(
        fps=fps,
        metadata={'title': 'EVEZ-OS Arc v3', 'artist': 'EVEZ666'},
        extra_args=['-vcodec','libx264','-pix_fmt','yuv420p',
                    '-crf','18','-preset','fast'])
    anim.save(out, writer=w, dpi=100)
    plt.close(fig)
    sz = os.path.getsize(out)/1e6
    print(f'DONE {out} ({sz:.2f}MB {TOTAL}fr)')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', default='/tmp/evez_cinematic.mp4')
    p.add_argument('--fps', type=int, default=30)
    p.add_argument('--spf', type=int, default=3,
                   help='frames per round')
    p.add_argument('--hold', type=float, default=4.0)
    a = p.parse_args()
    render(a.output, fps=a.fps, spf=a.spf, hold=a.hold)

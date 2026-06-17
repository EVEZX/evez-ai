// EVEZ VCL Renderer — node-canvas 2D, all 5 VCL physics engines
import { createCanvas } from '@napi-rs/canvas';

export const W = 1920, H = 1080;

export function createRenderer(cfg) {
  const canvas = createCanvas(W, H);
  const ctx = canvas.getContext('2d');
  const state = { particles: [], frame: 0, time: 0 };
  _init(state, cfg);
  return {
    renderFrame: (params) => _frame(ctx, state, cfg, params),
    getBuffer: () => canvas.toBuffer('raw'),
  };
}

function _init(s, cfg) {
  const n = cfg.physics.nodeCount || 200;
  s.particles = Array.from({ length: n }, (_, i) => ({
    x: Math.random() * W, y: Math.random() * H,
    vx: (Math.random() - 0.5) * 2, vy: (Math.random() - 0.5) * 2,
    mass: 1 + Math.random() * 3, energy: Math.random(),
    type: Math.random() > 0.5 ? 1 : -1, layer: 0, age: Math.random() * 500,
  }));
}

function _col(pal, idx, a) {
  const c = pal[((idx % pal.length) + pal.length) % pal.length];
  return `rgba(${c[0]},${c[1]},${c[2]},${a})`;
}

function _glow(ctx, x, y, r, pal, idx, a) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, _col(pal, idx, a));
  g.addColorStop(1, _col(pal, idx, 0));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
}

function _frame(ctx, s, cfg, params) {
  const [br, bg, bb] = cfg.visual.bg;
  ctx.fillStyle = `rgba(${br},${bg},${bb},${1 - cfg.visual.trailLength})`;
  ctx.fillRect(0, 0, W, H);
  s.frame++; s.time += 0.016;

  // Resize particle array if nodeCount changed
  const n = params.nodeCount || cfg.physics.nodeCount;
  while (s.particles.length < n) s.particles.push({
    x: Math.random() * W, y: Math.random() * H,
    vx: (Math.random() - 0.5) * 2, vy: (Math.random() - 0.5) * 2,
    mass: 1 + Math.random() * 3, energy: Math.random(),
    type: Math.random() > 0.5 ? 1 : -1, layer: 0, age: 0,
  });
  if (s.particles.length > n + 20) s.particles.length = n;

  switch (cfg.id) {
    case 'fire':   _fire(ctx, s, cfg, params);   break;
    case 'ocean':  _ocean(ctx, s, cfg, params);  break;
    case 'neural': _neural(ctx, s, cfg, params); break;
    case 'void':   _void(ctx, s, cfg, params);   break;
    case 'prime':  _prime(ctx, s, cfg, params);  break;
  }

  _hud(ctx, s, cfg);
}

// ─── FIRE ────────────────────────────────────────────────────────────────────
function _fire(ctx, s, cfg, p) {
  const G = p.gravitational_constant || -800, rep = p.repulsion || 2200;
  const fp = p.fire_cascade_prob || 0.018, damp = p.damping || 0.92, ms = p.maxSpeed || 6.5;
  const cx = W / 2 + Math.sin(s.time * 0.1) * 200;
  const cy = H / 2 + Math.cos(s.time * 0.08) * 120;
  const pal = cfg.visual.palette;

  for (const pi of s.particles) {
    const dx = cx - pi.x, dy = cy - pi.y, d = Math.hypot(dx, dy) + 1;
    let fx = (G / (d * d)) * dx / d * pi.mass;
    let fy = (G / (d * d)) * dy / d * pi.mass;

    for (let j = 0; j < s.particles.length; j += 4) {
      const pj = s.particles[j];
      const rx = pi.x - pj.x, ry = pi.y - pj.y;
      const rd = Math.hypot(rx, ry) + 5;
      if (rd < 110) { fx += (rep / (rd * rd)) * rx / rd; fy += (rep / (rd * rd)) * ry / rd; }
    }

    if (Math.random() < fp) {
      pi.energy = 1.0;
      const a = Math.random() * Math.PI * 2;
      fx += Math.cos(a) * 12; fy += Math.sin(a) * 12;
    }

    pi.vx = (pi.vx + fx * 0.01) * damp; pi.vy = (pi.vy + fy * 0.01) * damp;
    const spd = Math.hypot(pi.vx, pi.vy);
    if (spd > ms) { pi.vx *= ms / spd; pi.vy *= ms / spd; }
    pi.x += pi.vx; pi.y += pi.vy;
    pi.energy = Math.max(0, pi.energy - 0.015); pi.age++;
    if (pi.x < 0) pi.x = W; if (pi.x > W) pi.x = 0;
    if (pi.y < 0) pi.y = H; if (pi.y > H) pi.y = 0;

    const r = cfg.visual.nodeSize[0] + pi.energy * cfg.visual.nodeSize[1];
    _glow(ctx, pi.x, pi.y, r + cfg.visual.glowRadius * pi.energy, pal, Math.floor(pi.energy * 4), 0.4 + pi.energy * 0.6);
  }
}

// ─── OCEAN ───────────────────────────────────────────────────────────────────
function _ocean(ctx, s, cfg, p) {
  const wf = p.waveFreq || 0.04, wa = p.waveAmplitude || 45;
  const fs = p.flowSpeed || 0.8, turb = p.turbulence || 0.3;
  const pal = cfg.visual.palette, t = s.time;

  for (const pi of s.particles) {
    const nx = pi.x / W, ny = pi.y / H;
    const wv = Math.sin(nx * 8 + t * 1.2) * wa + Math.sin(ny * 6 + nx * 3 + t * 0.8) * wa * 0.6 + Math.cos(nx * 12 - ny * 8 + t * 1.5) * wa * 0.3;
    pi.vx = pi.vx * 0.88 + (fs + Math.sin(t * 0.3 + ny * 4) * 0.5) * 0.12 + (Math.random() - 0.5) * turb;
    pi.vy = pi.vy * 0.88 + (wv - pi.vy) * wf;
    pi.x += pi.vx; pi.y += pi.vy;
    pi.energy = (Math.sin(pi.x * 0.01 + t) + 1) / 2;
    if (pi.x < -50) pi.x = W + 50; if (pi.x > W + 50) pi.x = -50;
    if (pi.y < 0) pi.y = H; if (pi.y > H) pi.y = 0;
    const r = 2 + pi.energy * 6, dep = pi.y / H;
    _glow(ctx, pi.x, pi.y, r + 15 * pi.energy, pal, Math.floor(dep * 4), 0.3 + pi.energy * 0.5 + (1 - dep) * 0.2);
  }
}

// ─── NEURAL ──────────────────────────────────────────────────────────────────
function _neural(ctx, s, cfg, p) {
  const fr = p.synapticFireRate || 0.06, ps = p.propagationSpeed || 4.2;
  const inh = p.inhibitionRate || 0.02, layers = Math.max(2, p.layers || 7);
  const pal = cfg.visual.palette, lw = W / (layers + 1);
  const perLayer = Math.ceil(s.particles.length / layers);

  for (let i = 0; i < s.particles.length; i++) {
    const pi = s.particles[i];
    pi.layer = Math.floor(i / perLayer);
    const tx = lw * (pi.layer + 1);
    const ty = H * 0.1 + (H * 0.8) * (i % perLayer) / perLayer;
    pi.x += (tx - pi.x) * 0.02; pi.y += (ty - pi.y) * 0.02;
    if (Math.random() < fr * Math.max(0.1, 1 - inh * pi.layer)) pi.energy = 1.0;
    pi.energy = Math.max(0, pi.energy - 0.04);

    if (pi.energy > 0.1 && pi.layer < layers - 1) {
      const next = s.particles.filter(q => q.layer === pi.layer + 1).slice(0, 3);
      for (const tgt of next) {
        ctx.strokeStyle = _col(pal, 1, pi.energy * 0.5);
        ctx.lineWidth = pi.energy * 1.5;
        ctx.beginPath(); ctx.moveTo(pi.x, pi.y); ctx.lineTo(tgt.x, tgt.y); ctx.stroke();
        if (Math.random() < ps * 0.08) tgt.energy = Math.max(tgt.energy, pi.energy * 0.7);
      }
    }
    const r = 2 + pi.energy * 7;
    _glow(ctx, pi.x, pi.y, r + 10, pal, Math.floor(pi.energy * 4), 0.7 + pi.energy * 0.3);
  }
}

// ─── VOID ────────────────────────────────────────────────────────────────────
function _void(ctx, s, cfg, p) {
  const unc = p.quantumUncertainty || 0.8, ann = p.annihilationRate || 0.004;
  const cre = p.creationRate || 0.005, dark = p.darkMatterPull || -1200;
  const ent = p.entanglementStrength || 0.6, pal = cfg.visual.palette;
  const cx = W / 2, cy = H / 2, maxN = p.nodeCount || 150;

  while (Math.random() < cre && s.particles.length < maxN) {
    s.particles.push({ x: cx + (Math.random() - 0.5) * 400, y: cy + (Math.random() - 0.5) * 300,
      vx: (Math.random() - 0.5) * 3, vy: (Math.random() - 0.5) * 3,
      mass: Math.random() * 2, energy: 1.0, type: Math.random() > 0.5 ? 1 : -1, layer: 0, age: 0 });
  }

  for (let i = s.particles.length - 1; i >= 0; i--) {
    const pi = s.particles[i];
    pi.vx += (Math.random() - 0.5) * unc * 2; pi.vy += (Math.random() - 0.5) * unc * 2;
    const dx = cx - pi.x, dy = cy - pi.y, d = Math.hypot(dx, dy) + 10;
    pi.vx += (dark / (d * d)) * dx * 0.001; pi.vy += (dark / (d * d)) * dy * 0.001;

    let near = null, nearD = 300;
    for (let j = 0; j < s.particles.length; j += 2) {
      if (j === i || s.particles[j].type === pi.type) continue;
      const ed = Math.hypot(s.particles[j].x - pi.x, s.particles[j].y - pi.y);
      if (ed < nearD) { near = s.particles[j]; nearD = ed; }
    }
    if (near) {
      pi.vx += (near.x - pi.x) * ent * 0.0005; pi.vy += (near.y - pi.y) * ent * 0.0005;
      if (nearD < 8 && Math.random() < ann * 5) {
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.beginPath(); ctx.arc(pi.x, pi.y, 18, 0, Math.PI * 2); ctx.fill();
        s.particles.splice(i, 1); continue;
      }
    }
    pi.vx *= 0.97; pi.vy *= 0.97;
    pi.x += pi.vx; pi.y += pi.vy;
    pi.energy = Math.max(0, pi.energy - 0.004); pi.age++;
    if (pi.age > 3000 && Math.random() < ann) { s.particles.splice(i, 1); continue; }
    const r = 1 + pi.energy * 10;
    _glow(ctx, pi.x, pi.y, r + 22, pal, pi.type > 0 ? 3 : 2, pi.energy * 0.85);
  }
}

// ─── PRIME ───────────────────────────────────────────────────────────────────
function _prime(ctx, s, cfg, p) {
  const orbSpd = p.orbitalSpeed || 0.003, sieveN = p.sieveDepth || 200;
  const cryst = p.crystallization || 0.4, extent = p.ulam_extent || 50;
  const pal = cfg.visual.palette, t = s.time;
  const cx = W / 2, cy = H / 2, scale = Math.min(W, H) * 0.42;

  const primes = _sieve(Math.max(sieveN, s.particles.length + 2));
  const pset = new Set(primes);

  for (let i = 0; i < s.particles.length; i++) {
    const pi = s.particles[i];
    const n = i + 1;
    const [ux, uy] = _ulam(n);
    const sc = scale / Math.max(10, extent);
    const tx = cx + ux * sc + Math.cos(t * orbSpd * 0.3 + i * 0.5) * (pset.has(n) ? 6 : 2);
    const ty = cy + uy * sc + Math.sin(t * orbSpd * 0.3 + i * 0.5) * (pset.has(n) ? 6 : 2);
    pi.x += (tx - pi.x) * cryst * 0.12; pi.y += (ty - pi.y) * cryst * 0.12;

    const isPrime = pset.has(n), isTwin = isPrime && (pset.has(n + 2) || pset.has(n - 2));
    pi.energy = isPrime ? 0.75 + Math.sin(t * 2.5 + i) * 0.25 : 0.2;
    const r = isPrime ? 4 + pi.energy * 7 : 2;
    const ci = isTwin ? 2 : (isPrime ? 0 : 1);
    _glow(ctx, pi.x, pi.y, r + (isPrime ? 12 : 3), pal, ci, isPrime ? 0.7 + pi.energy * 0.3 : 0.12);

    if (isTwin) {
      const twinPos = primes.indexOf(n + 2);
      if (twinPos >= 0 && twinPos < s.particles.length) {
        const tgt = s.particles[twinPos];
        ctx.strokeStyle = _col(pal, 2, 0.25);
        ctx.lineWidth = 0.8;
        ctx.beginPath(); ctx.moveTo(pi.x, pi.y); ctx.lineTo(tgt.x, tgt.y); ctx.stroke();
      }
    }
  }
}

function _sieve(n) {
  const a = new Uint8Array(n + 1).fill(1); a[0] = a[1] = 0;
  for (let i = 2; i * i <= n; i++) if (a[i]) for (let j = i * i; j <= n; j += i) a[j] = 0;
  return [...a.keys()].filter(i => a[i]);
}

function _ulam(n) {
  if (n <= 1) return [0, 0];
  let x = 0, y = 0, dx = 0, dy = -1, ring = 1;
  for (let i = 1; i < n; i++) {
    x += dx; y += dy;
    if (x === ring && y === -(ring)) { dx = 0; dy = 1; }
    else if (x === -(ring) && y === ring) { dx = 1; dy = 0; ring++; }
    else if (x === ring && y === ring) { dx = -1; dy = 0; }
    else if (x === -(ring) && y === -(ring)) { dx = 0; dy = -1; }
  }
  return [x, y];
}

// ─── HUD ─────────────────────────────────────────────────────────────────────
function _hud(ctx, s, cfg) {
  ctx.fillStyle = 'rgba(0,255,65,0.65)';
  ctx.font = 'bold 16px monospace';
  ctx.fillText(cfg.name, 18, 32);
  ctx.fillStyle = 'rgba(0,180,40,0.35)';
  ctx.font = '11px monospace';
  ctx.fillText(`FRAME ${s.frame} | EVEZ-OS | openclaw-evezx.vercel.app`, 18, 50);
  const pulse = (Math.sin(s.time * 2.5) + 1) / 2;
  ctx.fillStyle = `rgba(255,30,30,${0.6 + pulse * 0.4})`;
  ctx.beginPath(); ctx.arc(W - 28, 22, 5, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.55)';
  ctx.font = '11px monospace';
  ctx.fillText('● LIVE', W - 76, 27);
}

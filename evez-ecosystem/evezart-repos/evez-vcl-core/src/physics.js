// EVEZ VCL Physics — FFmpeg nullsrc + vf geq filter expressions
// params: { energy, chaos, speed, scale, mood }  all in [0.0, 2.0]

export function buildFFmpegArgs(vcl, p = {}, rtmpUrl) {
  const e  = Math.max(0.01, p.energy ?? 1.0);
  const c  = Math.max(0.01, p.chaos  ?? 0.5);
  const s  = Math.max(0.01, p.speed  ?? 1.0);
  const m  = Math.max(0.01, p.mood   ?? 0.5);

  // Each VCL has unique geq r/g/b math expressions
  const geqFilters = {
    fire:
      `format=rgb24,geq=` +
      `r='clip(255*(0.5+0.5*sin(X/${(12/e).toFixed(2)}-T*${(s*1.0).toFixed(3)})*sin(Y/${(8/e).toFixed(2)}+T*${(s*1.3*c).toFixed(3)})+${e.toFixed(3)}*0.3*sin((X*X+Y*Y)/50000-T*${(s*2).toFixed(3)})),0,255)':` +
      `g='clip(180*(0.3+0.4*sin(X/${(15/e).toFixed(2)}+T*${(s*0.7).toFixed(3)})*cos(Y/${(10/e).toFixed(2)}-T*${s.toFixed(3)})*${c.toFixed(3)}),0,255)':` +
      `b='clip(60*(0.1+0.2*cos(X/${(20/e).toFixed(2)}-T*${(s*1.5).toFixed(3)})*sin(Y/${(18/e).toFixed(2)}+T*${s.toFixed(3)})*${m.toFixed(3)}),0,255)'`,

    ocean:
      `format=rgb24,geq=` +
      `r='clip(20+30*sin(X/${(40/e).toFixed(2)}+T*${s.toFixed(3)})*sin(Y/${(30/e).toFixed(2)}-T*${(s*0.6).toFixed(3)})*${c.toFixed(3)},0,255)':` +
      `g='clip(80+175*(0.5+0.5*sin(X/${(20/e).toFixed(2)}+T*${(s*1.2).toFixed(3)})*cos(Y/${(15/e).toFixed(2)}+T*${s.toFixed(3)})+${(e*0.25).toFixed(3)}*sin((X+Y)/${(25/e).toFixed(2)}-T*${(s*1.7).toFixed(3)})),0,255)':` +
      `b='clip(120+135*(0.5+0.5*cos(X/${(18/e).toFixed(2)}-T*${s.toFixed(3)})*sin(Y/${(22/e).toFixed(2)}+T*${(s*0.8).toFixed(3)})*${e.toFixed(3)}+0.3*sin((X-Y)/${(30/e).toFixed(2)}+T*${(s*2.1*c).toFixed(3)})),0,255)'`,

    neural:
      `format=rgb24,geq=` +
      `r='clip(60+195*(0.5+0.5*sin(X/${(10/e).toFixed(2)}+T*${s.toFixed(3)})*sin(Y/${(10/e).toFixed(2)}+T*${s.toFixed(3)})+0.3*sin(sqrt((X-640)*(X-640)+(Y-360)*(Y-360))/${(20/e).toFixed(2)}-T*${(s*1.5).toFixed(3)})*${c.toFixed(3)}),0,255)':` +
      `g='clip(0+80*(0.5+0.5*sin((X*${c.toFixed(3)}+Y*${e.toFixed(3)})/${(15/e).toFixed(2)}+T*${(s*2).toFixed(3)})),0,255)':` +
      `b='clip(80+175*(0.5+0.5*cos(X/${(12/e).toFixed(2)}-T*${(s*0.9).toFixed(3)})*cos(Y/${(12/e).toFixed(2)}+T*${s.toFixed(3)})+${(e*0.4).toFixed(3)}*sin((X+Y)/${(8/e).toFixed(2)}-T*${(s*3*c).toFixed(3)})),0,255)'`,

    void:
      `format=rgb24,geq=` +
      `r='clip(255*(0.5+0.5*sin(X/${(8/e).toFixed(2)}+T*${s.toFixed(3)})*sin(Y/${(8/e).toFixed(2)}+T*${s.toFixed(3)})*sin((X+Y)/${(6/e).toFixed(2)}-T*${(s*2).toFixed(3)})*${(c*m).toFixed(3)}),0,255)':` +
      `g='clip(255*(0.5+0.5*sin(X/${(9/e).toFixed(2)}-T*${(s*1.1).toFixed(3)})*cos(Y/${(7/e).toFixed(2)}+T*${s.toFixed(3)})*cos(X*Y/100000-T*${(s*1.5).toFixed(3)})*${c.toFixed(3)}),0,255)':` +
      `b='clip(255*(0.5+0.5*cos(X/${(10/e).toFixed(2)}+T*${(s*0.8).toFixed(3)})*sin(Y/${(9/e).toFixed(2)}-T*${s.toFixed(3)})+${(e*0.5).toFixed(3)}*sin(sqrt((X-640)*(X-640)+(Y-360)*(Y-360))/${(15/e).toFixed(2)}-T*${(s*2.5*c).toFixed(3)})),0,255)'`,

    prime:
      `format=rgb24,geq=` +
      `r='clip(255*(0.5+0.5*sin(X/${(7/e).toFixed(2)}+T*${s.toFixed(3)}+sin(Y/${(13/e).toFixed(2)})*${c.toFixed(3)})*sin((X-640)/${(5/e).toFixed(2)}+(Y-360)/${(8/e).toFixed(2)}+T*${(s*1.618).toFixed(3)})),0,255)':` +
      `g='clip(180*(0.5+0.5*sin(X/${(11/e).toFixed(2)}-T*${(s*0.618).toFixed(3)})*cos((X*X+Y*Y)/200000-T*${s.toFixed(3)})*${(c*e).toFixed(3)}),0,255)':` +
      `b='clip(255*(0.5+0.5*cos(X/${(9/e).toFixed(2)}+T*${(s*1.414).toFixed(3)})*sin(Y/${(6/e).toFixed(2)}-T*${s.toFixed(3)})+0.4*sin((X+Y*${c.toFixed(3)})/${(10/e).toFixed(2)}-T*${(s*2).toFixed(3)})),0,255)'`,
  };

  const geq = geqFilters[vcl] || geqFilters.fire;

  return [
    '-f', 'lavfi', '-i', 'nullsrc=size=1280x720:rate=30',
    '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
    '-vf', geq,
    '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency',
    '-b:v', '2500k', '-maxrate', '2500k', '-bufsize', '5000k',
    '-pix_fmt', 'yuv420p', '-g', '60', '-keyint_min', '60',
    '-x264opts', 'no-scenecut',
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-map', '0:v', '-map', '1:a',
    '-f', 'flv', rtmpUrl,
  ];
}

export function keywordToParams(keyword, current = {}) {
  const kw = keyword.toLowerCase().trim();
  const p  = { ...current };
  const M  = {
    fire:    { energy: 1.8, speed: 1.5, chaos: 0.8, mood: 0.9 },
    explode: { energy: 2.0, speed: 2.0, chaos: 1.5, mood: 1.0 },
    calm:    { energy: 0.5, speed: 0.4, chaos: 0.2, mood: 0.1 },
    chaos:   { chaos: 1.8,  speed: 1.8, mood: 1.0 },
    order:   { chaos: 0.1,  speed: 0.5, mood: 0.0 },
    fast:    { speed: 2.0 },
    slow:    { speed: 0.2 },
    grow:    { energy: Math.min((p.energy || 1) + 0.3, 2.0) },
    wave:    { energy: 1.2, speed: 0.8, chaos: 0.6 },
    storm:   { energy: 1.8, speed: 1.5, chaos: 1.5 },
    still:   { energy: 0.3, speed: 0.3, chaos: 0.1 },
    deep:    { energy: 0.8, speed: 0.5, chaos: 0.3 },
    flow:    { speed: 0.9,  chaos: 0.4 },
    surge:   { energy: 1.6, speed: 1.4, chaos: 1.0 },
    think:   { energy: 1.0, speed: 0.8, chaos: 0.4 },
    learn:   { energy: 1.1, speed: 0.9, chaos: 0.5 },
    forget:  { energy: 0.4, speed: 0.3, chaos: 0.2 },
    focus:   { energy: 1.3, speed: 1.0, chaos: 0.2 },
    dream:   { energy: 0.7, speed: 0.5, chaos: 0.8 },
    void:    { energy: 0.3, speed: 0.2, chaos: 0.1, mood: 0.0 },
    create:  { energy: 1.5, speed: 1.2, chaos: 0.7 },
    destroy: { energy: 2.0, speed: 2.0, chaos: 2.0, mood: 1.0 },
    entangle:{ chaos: 1.2,  energy: 1.1, speed: 0.7 },
    collapse:{ energy: 0.2, speed: 2.0, chaos: 2.0, mood: 1.0 },
    expand:  { energy: 1.8, speed: 0.5, chaos: 0.3 },
    nothing: { energy: 0.1, speed: 0.1, chaos: 0.0, mood: 0.0 },
    prime:   { energy: 1.2, speed: 0.7, chaos: 0.3 },
    spiral:  { speed: 0.6,  chaos: 0.4, energy: 1.0 },
    golden:  { energy: 1.618, speed: 0.618, chaos: 0.382 },
    orbit:   { speed: 1.0,  energy: 1.0, chaos: 0.5 },
    crystal: { energy: 0.8, speed: 0.3, chaos: 0.1 },
    infinity:{ energy: 1.0, speed: 1.0, chaos: 1.0 },
  };
  return M[kw] ? { ...p, ...M[kw] } : p;
}

export function sentimentToParams(sentiment, current = {}) {
  return {
    ...current,
    mood:  Math.max(0.01, Math.min(2.0, 1.0 - sentiment)),
    chaos: Math.max(0.01, Math.min(2.0, 0.5 + (1 - sentiment) * 0.5)),
  };
}

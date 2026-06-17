// EVEZ VCL Configuration Registry
// Each VCL: unique physics, aesthetics, and sensory keyword-to-param mappings.

export const VCL_REGISTRY = {
  fire: {
    id: 'fire', name: 'EVEZ VCL-1: FIRE',
    broadcastId: 'HZ1Ky2LxPQQ',
    liveChatId: 'KicKGFVDMnBpb1BiaW51TTk0YkQ3LWZOaEZnURILSFoxS3kyTHhQUVE',
    streamKey: process.env.STREAM_KEY_FIRE || '85db-3cyg-f6hx-u7th-fw3c',
    physics: {
      nodeCount: 220, gravitational_constant: -800, repulsion: 2200,
      fire_cascade_prob: 0.018, damping: 0.92, maxSpeed: 6.5,
    },
    visual: {
      bg: [2, 4, 3], glowRadius: 18, trailLength: 0.88, nodeSize: [2, 8],
      palette: [[255,102,0],[255,200,0],[255,40,0],[0,255,65],[255,255,255]],
    },
    sensory: {
      keywords: {
        fire: { fire_cascade_prob: 0.015 }, explode: { repulsion: 500, fire_cascade_prob: 0.03 },
        calm: { fire_cascade_prob: -0.01, repulsion: -200 }, grow: { nodeCount: 15 },
        fast: { maxSpeed: 2 }, slow: { maxSpeed: -2 },
        chaos: { gravitational_constant: -400, repulsion: 800 },
        order: { gravitational_constant: 200, repulsion: -300 },
      },
      viewerEffect: (n, p) => { p.nodeCount = Math.min(400, 150 + Math.floor(n * 0.8)); p.gravitational_constant = -600 - n * 2; },
      sentimentEffect: (s, p) => { if (s > 0.6) p.fire_cascade_prob += 0.005; if (s < 0.3) p.fire_cascade_prob = Math.max(0.005, p.fire_cascade_prob - 0.005); },
    }
  },

  ocean: {
    id: 'ocean', name: 'EVEZ VCL-2: OCEAN',
    broadcastId: 'd2djg_HibKI',
    liveChatId: 'KicKGFVDMnBpb1BiaW51TTk0YkQ3LWZOaEZnURILZDJkamdfSGliS0k',
    streamKey: process.env.STREAM_KEY_OCEAN || 'kjhx-h3rr-f1p8-8bht-asa4',
    physics: {
      nodeCount: 300, waveFreq: 0.04, waveAmplitude: 45,
      flowSpeed: 0.8, turbulence: 0.3, currentStrength: 1.2,
    },
    visual: {
      bg: [0, 8, 20], glowRadius: 22, trailLength: 0.94, nodeSize: [3, 9],
      palette: [[0,150,255],[0,229,255],[0,80,180],[100,220,255],[180,255,255]],
    },
    sensory: {
      keywords: {
        wave: { waveAmplitude: 20 }, calm: { turbulence: -0.15, waveAmplitude: -15 },
        storm: { turbulence: 0.4, waveAmplitude: 40 },
        flow: { flowSpeed: 0.5, currentStrength: 0.5 },
        still: { flowSpeed: -0.3, turbulence: -0.2 },
        deep: { nodeCount: 50 }, surge: { currentStrength: 0.8 },
      },
      viewerEffect: (n, p) => { p.waveAmplitude = 30 + n * 0.5; p.nodeCount = Math.min(500, 200 + n); },
      sentimentEffect: (s, p) => { p.turbulence = Math.max(0.05, 0.2 + (1 - s) * 0.4); },
    }
  },

  neural: {
    id: 'neural', name: 'EVEZ VCL-3: NEURAL',
    broadcastId: '0RRzjMf9LH4',
    liveChatId: 'KicKGFVDMnBpb1BiaW51TTk0YkQ3LWZOaEZnURILMFJSempNZjlMSDQ',
    streamKey: process.env.STREAM_KEY_NEURAL || '7pdw-1tas-p995-f75p-c0z8',
    physics: {
      nodeCount: 180, layers: 7, synapticFireRate: 0.06,
      propagationSpeed: 4.2, inhibitionRate: 0.02, plasticityRate: 0.001, recurrentStrength: 0.4,
    },
    visual: {
      bg: [4, 0, 12], glowRadius: 14, trailLength: 0.82, nodeSize: [2, 6],
      palette: [[119,51,255],[0,229,255],[255,255,255],[200,100,255],[80,0,180]],
    },
    sensory: {
      keywords: {
        think: { synapticFireRate: 0.02 }, learn: { plasticityRate: 0.002 },
        forget: { plasticityRate: -0.001, recurrentStrength: -0.1 },
        focus: { inhibitionRate: 0.01, propagationSpeed: 1 },
        dream: { recurrentStrength: 0.3, inhibitionRate: -0.01 },
        fire: { synapticFireRate: 0.05 }, grow: { nodeCount: 20, layers: 1 },
      },
      viewerEffect: (n, p) => { p.synapticFireRate = 0.04 + n * 0.002; p.layers = Math.min(12, 5 + Math.floor(n / 10)); },
      sentimentEffect: (s, p) => { p.propagationSpeed = 2 + s * 4; },
    }
  },

  void: {
    id: 'void', name: 'EVEZ VCL-4: VOID',
    broadcastId: 'kFcxBgsqEKM',
    liveChatId: 'KicKGFVDMnBpb1BiaW51TTk0YkQ3LWZOaEZnURILa0ZjeEJnc3FFS00',
    streamKey: process.env.STREAM_KEY_VOID || 'xqrp-4a9b-kup0-2gtx-66mt',
    physics: {
      nodeCount: 150, quantumUncertainty: 0.8, annihilationRate: 0.004,
      creationRate: 0.005, darkMatterPull: -1200, entanglementStrength: 0.6,
    },
    visual: {
      bg: [1, 1, 2], glowRadius: 30, trailLength: 0.97, nodeSize: [1, 12],
      palette: [[20,0,40],[100,0,200],[180,180,255],[255,255,255],[0,100,150]],
    },
    sensory: {
      keywords: {
        void: { annihilationRate: 0.003 }, create: { creationRate: 0.006 },
        destroy: { annihilationRate: 0.008 }, entangle: { entanglementStrength: 0.2 },
        collapse: { quantumUncertainty: -0.3, darkMatterPull: -800 },
        expand: { darkMatterPull: 400, creationRate: 0.003 }, nothing: { nodeCount: -10 },
      },
      viewerEffect: (n, p) => { p.quantumUncertainty = Math.max(0.1, 0.9 - n * 0.02); p.annihilationRate = 0.002 + n * 0.0003; },
      sentimentEffect: (s, p) => { p.darkMatterPull = -800 - (1 - s) * 800; },
    }
  },

  prime: {
    id: 'prime', name: 'EVEZ VCL-5: PRIME',
    broadcastId: 'OvuJfjmMIc4',
    liveChatId: 'KicKGFVDMnBpb1BiaW51TTk0YkQ3LWZOaEZnURILT3Z1SmZqbU1JYzQ',
    streamKey: process.env.STREAM_KEY_PRIME || 'cw0w-rxv5-shgx-2db0-8p4s',
    physics: {
      nodeCount: 260, spiralDensity: 1.618, primeHighlightRate: 0.12,
      ulam_extent: 50, orbitalSpeed: 0.003, sieveDepth: 200, crystallization: 0.4,
    },
    visual: {
      bg: [3, 3, 8], glowRadius: 16, trailLength: 0.91, nodeSize: [2, 10],
      palette: [[230,180,40],[255,255,200],[180,120,0],[255,100,150],[0,200,100]],
    },
    sensory: {
      keywords: {
        prime: { primeHighlightRate: 0.05, sieveDepth: 50 }, spiral: { spiralDensity: 0.1 },
        golden: { spiralDensity: 0.2 }, orbit: { orbitalSpeed: 0.002 },
        crystal: { crystallization: 0.2 }, chaos: { crystallization: -0.3, orbitalSpeed: 0.005 },
        infinity: { sieveDepth: 100, ulam_extent: 20 },
      },
      viewerEffect: (n, p) => { p.sieveDepth = 100 + n * 2; p.ulam_extent = 30 + Math.floor(n / 2); },
      sentimentEffect: (s, p) => { p.crystallization = Math.max(0.05, 0.2 + s * 0.6); },
    }
  },
};

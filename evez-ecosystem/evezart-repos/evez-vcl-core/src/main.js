// EVEZ VCL Main — pure FFmpeg streaming, zero native deps
import { spawn } from 'child_process';
import { buildFFmpegArgs, keywordToParams, sentimentToParams } from './physics.js';
import { loadBrain, saveBrain, logSensory } from './brain.js';
import { getLiveChatId, fetchChatMessages, getViewerCount, analyzeSentiment } from './sensory.js';

const VCL_ID = process.env.VCL_ID || 'fire';
const BROADCAST_IDS = {
  fire:   'HZ1Ky2LxPQQ',
  ocean:  'd2djg_HibKI',
  neural: '0RRzjMf9LH4',
  void:   'kFcxBgsqEKM',
  prime:  'OvuJfjmMIc4',
};
const STREAM_KEYS = {
  fire:   process.env.STREAM_KEY_FIRE,
  ocean:  process.env.STREAM_KEY_OCEAN,
  neural: process.env.STREAM_KEY_NEURAL,
  void:   process.env.STREAM_KEY_VOID,
  prime:  process.env.STREAM_KEY_PRIME,
};
const RTMP_BASE   = 'rtmp://a.rtmp.youtube.com/live2';
const BROADCAST_ID = BROADCAST_IDS[VCL_ID];
const STREAM_KEY   = STREAM_KEYS[VCL_ID];

if (!STREAM_KEY) {
  console.error(`[vcl] FATAL: STREAM_KEY_${VCL_ID.toUpperCase()} not set`);
  process.exit(1);
}

const RTMP_URL = `${RTMP_BASE}/${STREAM_KEY}`;
console.log(`\n╔═══════════════════════════════════╗`);
console.log(`║  EVEZ VCL-${VCL_ID.toUpperCase().padEnd(5)} STREAMING ENGINE  ║`);
console.log(`╚═══════════════════════════════════╝\n`);

let params = {};
let ffmpegProc = null;
let restartCount = 0;
let pendingRestart = false;

function spawnFFmpeg(currentParams) {
  const args = buildFFmpegArgs(VCL_ID, currentParams, RTMP_URL);
  console.log(`[vcl] spawning ffmpeg (restart #${restartCount})...`);

  const proc = spawn('ffmpeg', args, { stdio: ['ignore', 'pipe', 'pipe'] });

  let lastFrameLog = 0;
  proc.stderr.on('data', d => {
    const line = d.toString();
    const now = Date.now();
    const progress = line.match(/frame=\s*(\d+)\s+fps=([\d.]+).*bitrate=([\d.]+)/);
    if (progress && now - lastFrameLog > 5000) {
      console.log(`[stream] frame=${progress[1]} fps=${progress[2]} bitrate=${progress[3]}kbps`);
      lastFrameLog = now;
    } else if (/error|failed|invalid/i.test(line) && !/Application provided/i.test(line)) {
      console.error('[ffmpeg]', line.trim().slice(0, 120));
    }
  });

  proc.on('exit', (code, signal) => {
    console.log(`[vcl] ffmpeg exit code=${code} signal=${signal}`);
    restartCount++;
    const delay = Math.min(restartCount * 2000, 15000);
    console.log(`[vcl] restarting in ${delay}ms...`);
    setTimeout(() => {
      ffmpegProc = spawnFFmpeg(params);
    }, delay);
  });

  return proc;
}

const KEYWORDS = [
  'fire','explode','calm','chaos','order','fast','slow','grow',
  'wave','storm','still','deep','flow','surge',
  'think','learn','forget','focus','dream',
  'void','create','destroy','entangle','collapse','expand','nothing',
  'prime','spiral','golden','orbit','crystal','infinity',
];

async function sensoryLoop() {
  const liveChatId = await getLiveChatId(BROADCAST_ID);
  console.log(`[sensory] liveChatId=${liveChatId || 'none (broadcast not live yet)'}`);

  let cycle = 0;

  setInterval(async () => {
    cycle++;
    try {
      const messages = liveChatId ? await fetchChatMessages(liveChatId) : [];
      const viewers  = await getViewerCount(BROADCAST_ID);
      let mutated = false;

      for (const msg of messages) {
        for (const kw of KEYWORDS) {
          if (msg.toLowerCase().includes(kw)) {
            const prev = JSON.stringify(params);
            params = keywordToParams(kw, params);
            if (JSON.stringify(params) !== prev) {
              console.log(`[sensory] "${kw}" → ${JSON.stringify(params)}`);
              mutated = true;
              await logSensory('keyword', { keyword: kw, message: msg.slice(0, 100) });
            }
            break;
          }
        }
      }

      if (viewers > 0) {
        params.energy = Math.max(0.5, Math.min(2.0, 0.8 + viewers * 0.04));
        console.log(`[sensory] viewers=${viewers} → energy=${params.energy.toFixed(2)}`);
      }

      if (cycle % 6 === 0 && messages.length > 0) {
        const sentiment = await analyzeSentiment(messages, process.env.GROQ_API_KEY);
        params = sentimentToParams(sentiment, params);
        console.log(`[sensory] sentiment=${sentiment.toFixed(2)}`);
        await logSensory('sentiment', { sentiment, params });
      }

      if (mutated && ffmpegProc && !pendingRestart) {
        pendingRestart = true;
        console.log('[vcl] physics mutation — respawning ffmpeg');
        ffmpegProc.kill('SIGTERM');
        setTimeout(() => { pendingRestart = false; }, 5000);
      }
    } catch (e) {
      console.error('[sensory]', e.message);
    }
  }, 10_000);

  setInterval(async () => {
    await saveBrain(params);
    console.log(`[brain] saved: ${JSON.stringify(params)}`);
  }, 60_000);
}

async function main() {
  params = await loadBrain();
  console.log(`[brain] loaded: ${JSON.stringify(params)}`);

  ffmpegProc = spawnFFmpeg(params);
  await sensoryLoop();

  process.on('SIGTERM', async () => {
    console.log('[vcl] SIGTERM — saving brain...');
    await saveBrain(params);
    ffmpegProc?.kill('SIGTERM');
    setTimeout(() => process.exit(0), 3000);
  });

  process.on('uncaughtException', e => {
    console.error('[vcl] uncaught:', e.message);
    // Don't exit — keep streaming
  });

  process.on('unhandledRejection', (r) => {
    console.error('[vcl] unhandled rejection:', r);
  });

  console.log(`[vcl] ${VCL_ID.toUpperCase()} STREAMING LIVE ✓`);
}

main().catch(e => {
  console.error('[vcl] fatal startup error:', e);
  process.exit(1);
});

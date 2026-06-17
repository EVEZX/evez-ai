// EVEZ VCL Streamer — FFmpeg RTMP pipeline with auto-restart
import { spawn } from 'child_process';
export const W = 1920, H = 1080, FPS = 30;

export class Streamer {
  constructor(key) { this.key = key; this.proc = null; this.dropped = 0; }

  start() {
    const url = `rtmp://a.rtmp.youtube.com/live2/${this.key}`;
    this.proc = spawn('ffmpeg', [
      '-y', '-f', 'rawvideo', '-pixel_format', 'rgba',
      '-video_size', `${W}x${H}`, '-framerate', `${FPS}`, '-i', 'pipe:0',
      '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
      '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency',
      '-b:v', '4000k', '-maxrate', '4500k', '-bufsize', '8000k',
      '-pix_fmt', 'yuv420p', '-g', String(FPS * 2), '-keyint_min', String(FPS),
      '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
      '-f', 'flv', '-reconnect', '1', '-reconnect_streamed', '1',
      '-reconnect_delay_max', '10', url,
    ], { stdio: ['pipe', 'pipe', 'pipe'] });

    this.proc.on('exit', (c, s) => {
      console.error(`[stream] ffmpeg exit code=${c} signal=${s} — restart in 5s`);
      setTimeout(() => this.start(), 5000);
    });
    this.proc.stderr.on('data', () => {}); // suppress stderr noise
    console.log(`[stream] ffmpeg → rtmp://.../${this.key.slice(0,8)}****`);
  }

  write(buf) {
    if (!this.proc?.stdin?.writable) return;
    try { this.proc.stdin.write(buf); } catch(e) { this.dropped++; }
  }

  stop() { try { this.proc?.stdin?.end(); this.proc?.kill('SIGTERM'); } catch(e) {} }
}

#!/usr/bin/env python3
"""EVEZ OpenClaw media workstation tools.

Generates DAW-friendly WAV samples, drum kits, SFZ instruments, loop previews,
ZIP packs, and optional waveform videos using only stdlib + optional ffmpeg.
"""
from __future__ import annotations
import argparse, json, math, os, random, shutil, struct, subprocess, sys, zipfile
from pathlib import Path
import wave

SR = 44100

def clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))

def write_wav(path: Path, samples: list[float], sr: int = SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        frames = b"".join(struct.pack("<h", int(clamp(s) * 32767)) for s in samples)
        w.writeframes(frames)

def read_wav_mono(path: Path) -> tuple[list[float], int]:
    with wave.open(str(path), "rb") as w:
        channels, width, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError(f"Only 16-bit PCM WAV supported for remix input: {path}")
    vals = struct.unpack("<" + "h" * (len(raw)//2), raw)
    mono = []
    if channels == 1:
        mono = [v/32768 for v in vals]
    else:
        for i in range(0, len(vals), channels):
            mono.append(sum(vals[i:i+channels]) / (channels * 32768))
    return mono, sr

def sine(freq: float, dur: float, amp: float = 1.0, sr: int = SR) -> list[float]:
    return [amp * math.sin(2 * math.pi * freq * i / sr) for i in range(int(dur * sr))]

def envelope(samples: list[float], attack=0.002, decay=0.2, sr: int = SR) -> list[float]:
    out=[]; a=max(1,int(attack*sr)); d=max(1,int(decay*sr)); n=len(samples)
    for i,s in enumerate(samples):
        if i<a: e=i/a
        else: e=math.exp(-(i-a)/d)
        # short release avoids clicks
        if i > n - int(0.01*sr): e *= max(0, (n-i)/max(1,int(0.01*sr)))
        out.append(s*e)
    return out

def kick() -> list[float]:
    n=int(0.55*SR); out=[]
    phase=0.0
    for i in range(n):
        t=i/SR
        freq=38 + 115*math.exp(-t*20)
        phase += 2*math.pi*freq/SR
        body=math.sin(phase)*math.exp(-t*7)
        click=(random.random()*2-1)*math.exp(-t*120)*0.25
        out.append((body+click)*0.9)
    return out

def snare() -> list[float]:
    n=int(0.38*SR); out=[]
    for i in range(n):
        t=i/SR
        noise=(random.random()*2-1)*math.exp(-t*16)
        tone=math.sin(2*math.pi*185*t)*math.exp(-t*12)
        out.append((noise*0.65 + tone*0.35)*0.75)
    return out

def hihat(closed=True) -> list[float]:
    dur=0.08 if closed else 0.32; n=int(dur*SR); out=[]
    last=0.0
    for i in range(n):
        t=i/SR
        # cheap highpass-ish metallic noise
        white=random.random()*2-1
        hp=white-last*0.92; last=white
        metal=math.sin(2*math.pi*7400*t)+0.7*math.sin(2*math.pi*9200*t)
        out.append((hp*0.7+metal*0.15)*math.exp(-t*(55 if closed else 10))*0.45)
    return out

def clap() -> list[float]:
    n=int(0.35*SR); out=[]
    bursts=[0.0,0.012,0.026,0.045]
    for i in range(n):
        t=i/SR
        env=sum(math.exp(-max(0,t-b)*70) if t>=b else 0 for b in bursts)
        out.append((random.random()*2-1)*env*0.28)
    return out

def bass_note(freq: float, dur: float=1.0) -> list[float]:
    out=[]; n=int(dur*SR)
    for i in range(n):
        t=i/SR
        saw=2*((freq*t)%1)-1
        sub=math.sin(2*math.pi*freq*t)
        e=min(1,t/0.02)*math.exp(-t/1.8)
        out.append((sub*0.75+saw*0.22)*e*0.7)
    return out

def mix_into(buf: list[float], src: list[float], start: int, gain: float=1.0):
    end=min(len(buf), start+len(src))
    for i in range(start,end):
        buf[i]=clamp(buf[i]+src[i-start]*gain)

def render_loop(drum_paths: dict[str, Path], out: Path, bpm=140, bars=4):
    beat=60/bpm; length=int(bars*4*beat*SR); buf=[0.0]*length
    samples={k: read_wav_mono(v)[0] for k,v in drum_paths.items()}
    for b in range(bars*4):
        pos=int(b*beat*SR)
        if b%4 in (0,2): mix_into(buf, samples['kick'], pos, 0.95)
        if b%4 in (1,3): mix_into(buf, samples['snare'], pos, 0.85)
        mix_into(buf, samples['hihat_closed'], pos, 0.45)
        mix_into(buf, samples['hihat_closed'], pos+int(0.5*beat*SR), 0.35)
        if b%8==7: mix_into(buf, samples['hihat_open'], pos+int(0.5*beat*SR), 0.4)
    write_wav(out, buf)

def make_sfz(path: Path, sample_dir: Path):
    rel = lambda p: os.path.relpath(p, path.parent).replace(os.sep, '/')
    lines=["// EVEZ OpenClaw generated SFZ drum/instrument map", "<group> lovel=1 hivel=127"]
    mapping=[(36,'kick.wav'),(38,'snare.wav'),(42,'hihat_closed.wav'),(46,'hihat_open.wav'),(39,'clap.wav')]
    for key, name in mapping:
        lines.append(f"<region> key={key} sample={rel(sample_dir/name)}")
    for key, note in [(36,'C2'),(43,'G2'),(48,'C3')]:
        sample=sample_dir/f"sub_{note}.wav"
        if sample.exists(): lines.append(f"<region> key={key} sample={rel(sample)}")
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text("\n".join(lines)+"\n")

def remix_input(src: Path, out_dir: Path, count=8):
    data, sr = read_wav_mono(src)
    if not data: return []
    out=[]; seg=max(1, len(data)//count)
    for i in range(count):
        chunk=data[i*seg:(i+1)*seg]
        if not chunk: continue
        if i%3==1: chunk=list(reversed(chunk))
        if i%3==2: chunk=chunk[::2] + chunk[1::2]
        # normalize and fade
        mx=max(0.01, max(abs(x) for x in chunk)); chunk=[x/mx*0.85 for x in chunk]
        chunk=envelope(chunk, attack=0.003, decay=max(0.02,len(chunk)/sr/2), sr=sr)
        p=out_dir/f"remix_slice_{i+1:02d}.wav"; write_wav(p, chunk, sr); out.append(p)
    return out

def zip_dir(src: Path, dest: Path):
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob('*')):
            if p.is_file() and p != dest:
                z.write(p, p.relative_to(src))

def render_video(audio: Path, mp4: Path) -> bool:
    if not shutil.which('ffmpeg'): return False
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(audio),'-filter_complex',
         '[0:a]showwaves=s=1280x720:mode=line:colors=00ffc8,format=yuv420p[v]',
         '-map','[v]','-map','0:a','-shortest','-c:v','libx264','-preset','veryfast','-c:a','aac',str(mp4)]
    return subprocess.run(cmd).returncode == 0

def generate(args):
    random.seed(args.seed)
    root=Path(args.out_dir).expanduser().resolve()/args.name
    samples=root/'Samples'; drums=samples/'Drums'; inst=samples/'Instruments'; loops=root/'Loops'; kits=root/'Kits'; previews=root/'Previews'
    for d in [drums,inst,loops,kits,previews]: d.mkdir(parents=True, exist_ok=True)
    drum_wavs={
      'kick': drums/'kick.wav', 'snare': drums/'snare.wav', 'hihat_closed': drums/'hihat_closed.wav', 'hihat_open': drums/'hihat_open.wav', 'clap': drums/'clap.wav'
    }
    write_wav(drum_wavs['kick'], kick()); write_wav(drum_wavs['snare'], snare()); write_wav(drum_wavs['hihat_closed'], hihat(True)); write_wav(drum_wavs['hihat_open'], hihat(False)); write_wav(drum_wavs['clap'], clap())
    for note,freq in [('C2',65.406),('G2',97.999),('C3',130.813)]: write_wav(inst/f'sub_{note}.wav', bass_note(freq))
    remixed=[]
    if args.remix:
        remixed=remix_input(Path(args.remix).expanduser(), drums, args.slices)
    loop=loops/f'{args.name}_{args.bpm}bpm_4bar.wav'; render_loop(drum_wavs, loop, bpm=args.bpm, bars=args.bars)
    sfz=kits/f'{args.name}.sfz'; make_sfz(sfz, samples)
    # DAW-friendly layout aliases
    (root/'FL_Studio_FPC').mkdir(exist_ok=True); (root/'StudioOne_ImpactXT').mkdir(exist_ok=True); (root/'Ableton_DrumRack').mkdir(exist_ok=True)
    for target in ['FL_Studio_FPC','StudioOne_ImpactXT','Ableton_DrumRack']:
        for wav in drums.glob('*.wav'):
            dst=root/target/wav.name
            if not dst.exists(): shutil.copy2(wav,dst)
    preview=previews/f'{args.name}_waveform.mp4'; video_ok=render_video(loop, preview)
    manifest={
      'name':args.name,'bpm':args.bpm,'sample_rate':SR,'format':['wav','sfz','zip'],
      'drum_samples':[str(p.relative_to(root)) for p in sorted(drums.glob('*.wav'))],
      'instrument_samples':[str(p.relative_to(root)) for p in sorted(inst.glob('*.wav'))],
      'sfz':str(sfz.relative_to(root)),'loop':str(loop.relative_to(root)),
      'preview_video':str(preview.relative_to(root)) if video_ok else None,
      'remixed_slices':[str(p.relative_to(root)) for p in remixed],
      'daw_layouts':['FL_Studio_FPC','StudioOne_ImpactXT','Ableton_DrumRack']
    }
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2))
    z=root.with_suffix('.zip'); zip_dir(root,z)
    result={'ok':True,'root':str(root),'zip':str(z),'loop':str(loop),'sfz':str(sfz),'preview_video':str(preview) if video_ok else None,'manifest':manifest}
    print(json.dumps(result, indent=2))

def main():
    ap=argparse.ArgumentParser(description='Generate OpenClaw DAW/sample/drum-kit media artifacts')
    ap.add_argument('--name', default='evez_openclaw_kit')
    ap.add_argument('--out-dir', default=os.environ.get('OPENCLAW_MEDIA_DIR','./media-out'))
    ap.add_argument('--bpm', type=int, default=140)
    ap.add_argument('--bars', type=int, default=4)
    ap.add_argument('--seed', type=int, default=666)
    ap.add_argument('--remix', help='Optional 16-bit PCM WAV to chop/remix into slices')
    ap.add_argument('--slices', type=int, default=8)
    args=ap.parse_args(); generate(args)
if __name__=='__main__': main()

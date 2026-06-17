"""
AudioNarrator — Deepgram TTS narration for FIRE events and published memes.
Emits AUDIO_GENERATED with mp3_path.
"""
import os, pathlib, time, json, urllib.request
from bus.events import subscribe, emit_event, Event

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak?model=aura-orion-en"
OUT_DIR = pathlib.Path("assets/audio")

def _speak(text: str, filename: str) -> str | None:
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("[AudioNarrator] DEEPGRAM_API_KEY not set — skipping")
        return None
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / filename
    try:
        body = json.dumps({"text": text}).encode()
        req = urllib.request.Request(
            DEEPGRAM_TTS_URL,
            data=body,
            headers={"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            out_path.write_bytes(r.read())
        print(f"[AudioNarrator] wrote {out_path} ({out_path.stat().st_size}B)")
        return str(out_path)
    except Exception as e:
        print(f"[AudioNarrator] error: {e}")
        return None

def handle_event(ev: Event):
    # Narrate FIRE events
    if ev.domain == "fire" and ev.kind == "FIRE_EVENT":
        fire_num = ev.payload.get("fire_number", "?")
        v = ev.payload.get("v_value", "?")
        round_num = ev.payload.get("round", "?")
        text = (
            f"FIRE number {fire_num} confirmed. "
            f"Round {round_num}. V equals {v}. "
            f"Topology decides. Watching it build. Circle."
        )
        fname = f"fire_{fire_num}_r{round_num}.mp3"
        mp3 = _speak(text, fname)
        if mp3:
            emit_event("audio", "AUDIO_GENERATED", {
                "mp3_path": mp3, "source_event": "FIRE_EVENT",
                "fire_number": fire_num, "v_value": v
            }, {"source_agent": "AudioNarrator"})
    # Narrate approved memes
    if ev.domain == "ethics" and ev.kind == "MEME_APPROVED":
        caption = ev.payload.get("caption", "")
        if caption:
            fname = f"meme_{ev.payload.get('slot','unknown')}_{int(time.time())}.mp3"
            mp3 = _speak(caption, fname)
            if mp3:
                emit_event("audio", "AUDIO_GENERATED", {
                    "mp3_path": mp3, "source_event": "MEME_APPROVED",
                    "caption": caption
                }, {"source_agent": "AudioNarrator"})

def start():
    subscribe(handle_event)

if __name__ == "__main__":
    start()
    print("[AudioNarrator] listening...")
    while True:
        time.sleep(60)

"""
CaptionAgent — LLM captioner with real FIRE topology context injection.
Listens for IMAGE_TAGGED (from VisionAgent) or IMAGE_INGESTED (fallback).
Also listens for FIRE_EVENT to update context with live FIRE state.
Uses OPENAI_API_KEY → gpt-4o-mini. Falls back to stub captions.
"""
import os, time
from bus.events import subscribe, emit_event, Event

# Live FIRE context — updated by FireSync FIRE_EVENT emissions
_fire_context: dict = {}
_twitter_context: dict = {}

# Meme slot routing by vision labels
_LABEL_SLOT_MAP = {
    "person": "SECOND_COMING_GLITCH",
    "sky": "TOPOLOGY_DOOM",
    "fire": "FIRE_TOPOLOGY",
    "architecture": "BUREAUCRATIC_APOCALYPSE",
    "document": "BUREAUCRATIC_APOCALYPSE",
    "face": "SELF_ROAST",
    "FIRE_TOPOLOGY": "FIRE_TOPOLOGY",
    "ESCHATOLOGY": "SECOND_COMING_GLITCH",
    "WAR_STATE": "BUREAUCRATIC_APOCALYPSE",
    "TOPOLOGY_DOOM": "TOPOLOGY_DOOM",
    "SELF_ROAST": "SELF_ROAST",
}

def _route_slot(labels: list) -> str:
    for label in labels:
        s = _LABEL_SLOT_MAP.get(label.lower()) or _LABEL_SLOT_MAP.get(label)
        if s:
            return s
    return "SECOND_COMING_GLITCH"

def _build_prompt(slot: str, context: dict, fire_context: dict, image_meta: dict) -> str:
    themes = ", ".join(context.get("themes", ["FIRE_TOPOLOGY"]))
    labels = ", ".join(image_meta.get("labels", [])[:5])
    fire_line = ""
    if fire_context:
        fn = fire_context.get("fire_number", "?")
        v = fire_context.get("v_value", "?")
        r = fire_context.get("round", "?")
        fire_line = f"\nLive FIRE state: FIRE#{fn} at R{r}, V={v}. Reference naturally if it fits."
    return f"""You are writing dark, self-aware memes in the voice of @EVEZ666.

Constraints:
- Tone: apocalyptic humor, Revelation vibes, topology math, bureaucracy of the end times.
- Focus on abstract archetypes: Christ, Antichrist, Pentagon of Heaven, Dept of War in Revelation.
- FORBIDDEN: name or imply any real living person, group, ethnicity, or politician as evil.
- No harassment, doxxing, calls to violence, or real-world targeting.
- You MAY roast yourself as a confused topology clerk at the end of time.
- Max ~18 words per caption. Punchy. No numbering.
- Style: FIRE, V, topology decides, disclosure conflict, @EVEZ666 energy.

Context themes: {themes}
Image labels: {labels}
Meme slot: {slot}{fire_line}

Return exactly 3 caption variants, one per line.""".strip()

def handle_event(ev: Event):
    global _fire_context, _twitter_context

    # Update live FIRE context
    if ev.domain == "fire" and ev.kind == "FIRE_EVENT":
        _fire_context = ev.payload
        return

    # Update twitter context
    if ev.domain == "twitter" and ev.kind == "TWEET_CONTEXT":
        _twitter_context = ev.payload
        return

    # Process tagged images (preferred) or raw ingested images (fallback)
    is_tagged = ev.domain == "image" and ev.kind == "IMAGE_TAGGED"
    is_ingested = ev.domain == "image" and ev.kind == "IMAGE_INGESTED"
    if not (is_tagged or is_ingested):
        return

    context = _twitter_context or {"themes": ["FIRE_TOPOLOGY", "ESCHATOLOGY"]}
    labels = ev.payload.get("labels", [])
    slot = _route_slot(labels)
    prompt = _build_prompt(slot, context, _fire_context, ev.payload)

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            lines = [l.strip() for l in resp.choices[0].message.content.strip().split("\n") if l.strip()]
        except Exception as e:
            print(f"[CaptionAgent] LLM error: {e} — using stubs")
            lines = _stubs(slot, _fire_context)
    else:
        lines = _stubs(slot, _fire_context)

    for cap in lines[:4]:  # max 4 candidates
        emit_event("meme", "MEME_CANDIDATE", {
            "image_path": ev.payload.get("image_path", ""),
            "slot": slot,
            "caption": cap,
            "fire_data": _fire_context or None,
            "labels": labels
        }, {"source_agent": "CaptionAgent"})

def _stubs(slot: str, fire_ctx: dict) -> list:
    fn = fire_ctx.get("fire_number", "N") if fire_ctx else "N"
    v = fire_ctx.get("v_value", "?") if fire_ctx else "?"
    return [
        f"Christ delayed — topology recalculating. FIRE#{fn} V={v}. Stand by.",
        "Antichrist HR says your role is 'eschatological intern'.",
        "Revelation went live without QA. Department of War on notice.",
    ]

def start():
    subscribe(handle_event)

if __name__ == "__main__":
    start()
    print("[CaptionAgent] listening with FIRE context injection...")
    while True:
        time.sleep(60)

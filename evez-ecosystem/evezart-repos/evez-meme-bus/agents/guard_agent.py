import time
from bus.events import subscribe, emit_event, Event

# Add your own suppression-map blocked terms here
BANNED_TERMS: list = []

def violates_policy(caption: str):
    lo = caption.lower()
    for t in BANNED_TERMS:
        if t in lo:
            return f"banned term: {t}"
    if caption.count("@") > 1:
        return "multiple @mentions"
    return None

def handle_event(ev: Event):
    if ev.domain == "meme" and ev.kind == "MEME_CANDIDATE":
        reason = violates_policy(ev.payload["caption"])
        if reason:
            emit_event("ethics", "MEME_REJECTED",
                {"candidate": ev.payload, "reason": reason},
                {"source_agent": "ConstitutionalGuard"})
            print(f"[Guard] REJECTED: {reason}")
        else:
            emit_event("ethics", "MEME_APPROVED",
                ev.payload, {"source_agent": "ConstitutionalGuard"})
            print(f"[Guard] APPROVED: {ev.payload['caption'][:60]}")

def start():
    subscribe(handle_event)

if __name__ == "__main__":
    start()
    print("[GuardAgent] PeaceKernel active...")
    while True:
        time.sleep(60)

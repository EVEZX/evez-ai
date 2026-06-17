import shutil, pathlib, time
from bus.events import subscribe, emit_event, Event

OUT = pathlib.Path("assets/output_memes")

def handle_event(ev: Event):
    if ev.domain == "ethics" and ev.kind == "MEME_APPROVED":
        src = pathlib.Path(ev.payload.get("image_path", ""))
        caption = ev.payload.get("caption", "")
        OUT.mkdir(parents=True, exist_ok=True)
        if src.exists():
            dst = OUT / src.name
            shutil.copy2(src, dst)
            (OUT / (src.stem + ".txt")).write_text(caption, encoding="utf-8")
            emit_event("publish", "MEME_PUBLISHED",
                {"output_path": str(dst), "caption": caption},
                {"source_agent": "Publisher"})
            print(f"[Publisher] published {dst}")
        else:
            draft = OUT / f"draft_{ev.payload.get('slot','unknown')}.txt"
            with draft.open("a", encoding="utf-8") as f:
                f.write(caption + "\n")
            print(f"[Publisher] caption draft saved: {caption[:60]}")

def start():
    subscribe(handle_event)

if __name__ == "__main__":
    start()
    print("[Publisher] ready...")
    while True:
        time.sleep(60)

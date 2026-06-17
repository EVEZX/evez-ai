import pathlib, time
from bus.events import emit_event

INPUT_DIR = pathlib.Path("assets/input_images")

def run_poll_loop(interval_sec: int = 60):
    seen: set = set()
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[ImageIngestor] watching", INPUT_DIR)
    while True:
        for p in INPUT_DIR.iterdir():
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                if p.name not in seen:
                    seen.add(p.name)
                    emit_event(
                        domain="image",
                        kind="IMAGE_INGESTED",
                        payload={"image_path": str(p), "filename": p.name},
                        meta={"source_agent": "ImageIngestor"}
                    )
                    print(f"[ImageIngestor] ingested {p.name}")
        time.sleep(interval_sec)

if __name__ == "__main__":
    run_poll_loop()

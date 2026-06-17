import pathlib, time
from bus.events import emit_event

CORPUS_DIR = pathlib.Path("assets/corpus_templates")

def run_poll_loop(interval_sec: int = 600):
    last_snapshot: set = set()
    print("[CorpusAgent] watching", CORPUS_DIR)
    while True:
        CORPUS_DIR.mkdir(parents=True, exist_ok=True)
        files = {p.name for p in CORPUS_DIR.iterdir() if p.is_file()}
        if files != last_snapshot:
            last_snapshot = files
            emit_event("corpus", "CORPUS_UPDATED",
                {"templates": list(files)},
                {"source_agent": "CorpusAgent"})
            print(f"[CorpusAgent] CORPUS_UPDATED: {len(files)} templates")
        time.sleep(interval_sec)

if __name__ == "__main__":
    run_poll_loop()

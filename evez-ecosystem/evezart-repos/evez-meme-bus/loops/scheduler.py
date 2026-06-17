import threading, time
import agents.image_ingestor as img_ing
import agents.twitter_context as tw_ctx
import agents.corpus_agent as corp
import agents.caption_agent as cap
import agents.guard_agent as guard
import agents.publisher as pub
import agents.layout_agent as layout

def start_all():
    cap.start()
    guard.start()
    pub.start()
    layout.start()
    threads = [
        threading.Thread(target=img_ing.run_poll_loop, daemon=True),
        threading.Thread(target=tw_ctx.run_poll_loop, daemon=True),
        threading.Thread(target=corp.run_poll_loop, daemon=True),
    ]
    for t in threads:
        t.start()
    print("[Scheduler] all agents running")
    while True:
        time.sleep(60)

if __name__ == "__main__":
    start_all()

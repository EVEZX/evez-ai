"""
VisionAgent — Google Cloud Vision image tagger.
Emits IMAGE_TAGGED event with labels/emotions/objects.
Falls back to filename heuristics if GCV unavailable.
"""
import os, pathlib, time, base64, json
from bus.events import subscribe, emit_event, Event

GCV_LABELS_URL = "https://vision.googleapis.com/v1/images:annotate"

def _gcv_tag(image_path: str) -> dict:
    api_key = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
    if not api_key:
        return _fallback_tag(image_path)
    try:
        import urllib.request
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        body = json.dumps({
            "requests": [{
                "image": {"content": b64},
                "features": [
                    {"type": "LABEL_DETECTION", "maxResults": 10},
                    {"type": "FACE_DETECTION", "maxResults": 5},
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                    {"type": "SAFE_SEARCH_DETECTION"}
                ]
            }]
        }).encode()
        req = urllib.request.Request(
            f"{GCV_LABELS_URL}?key={api_key}",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        r = resp.get("responses", [{}])[0]
        labels = [a["description"] for a in r.get("labelAnnotations", [])]
        objects = [o["name"] for o in r.get("localizedObjectAnnotations", [])]
        faces = len(r.get("faceAnnotations", []))
        safe = r.get("safeSearchAnnotation", {})
        return {"labels": labels, "objects": objects, "faces": faces, "safe_search": safe, "source": "gcv"}
    except Exception as e:
        print(f"[VisionAgent] GCV error: {e} — falling back")
        return _fallback_tag(image_path)

def _fallback_tag(image_path: str) -> dict:
    name = pathlib.Path(image_path).stem.lower()
    tags = []
    slot_hints = {
        "christ": "SECOND_COMING", "fire": "FIRE_TOPOLOGY", "war": "WAR_STATE",
        "angel": "ESCHATOLOGY", "topology": "TOPOLOGY_DOOM", "evez": "SELF_ROAST"
    }
    for k, v in slot_hints.items():
        if k in name:
            tags.append(v)
    return {"labels": tags or ["UNKNOWN"], "objects": [], "faces": 0, "safe_search": {}, "source": "fallback"}

def handle_event(ev: Event):
    if ev.domain == "image" and ev.kind == "IMAGE_INGESTED":
        path = ev.payload.get("image_path", "")
        if pathlib.Path(path).exists():
            tags = _gcv_tag(path)
            emit_event("image", "IMAGE_TAGGED", {
                **ev.payload, **tags
            }, {"source_agent": "VisionAgent"})
            print(f"[VisionAgent] tagged {path}: {tags['labels'][:3]}")

def start():
    subscribe(handle_event)

if __name__ == "__main__":
    start()
    print("[VisionAgent] listening...")
    while True:
        time.sleep(60)

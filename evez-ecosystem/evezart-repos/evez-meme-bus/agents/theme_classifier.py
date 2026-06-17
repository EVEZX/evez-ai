"""Tags incoming images with meme slots based on filename + active context themes."""
from bus.events import subscribe, emit_event, Event

SLOT_MAP = {
    "FIRE_TOPOLOGY": "TOPOLOGY_DOOM",
    "ESCHATOLOGY": "SECOND_COMING_GLITCH",
    "WAR_STATE": "BUREAUCRATIC_APOCALYPSE",
    "YHWH_DECODE": "ANTICHRIST_SELF_DEPRECATING",
    "DISCLOSURE": "DISCLOSURE_HUMOR",
    "TOPOLOGY_DECIDES": "TOPOLOGY_DOOM",
}

_active_themes: list[str] = ["FIRE_TOPOLOGY", "ESCHATOLOGY"]

def _get_slot(themes: list[str]) -> str:
    for theme in themes:
        if theme in SLOT_MAP:
            return SLOT_MAP[theme]
    return "GENERIC_END_TIMES"

def handle_event(ev: Event):
    global _active_themes
    if ev.domain == "twitter" and ev.kind == "TWEET_CONTEXT":
        _active_themes = ev.payload.get("themes", _active_themes)

    if ev.domain == "image" and ev.kind == "IMAGE_INGESTED":
        slot = _get_slot(_active_themes)
        emit_event(
            domain="image",
            kind="IMAGE_CLASSIFIED",
            payload={**ev.payload, "slot": slot, "active_themes": _active_themes},
            meta={"source_agent": "ThemeClassifier"}
        )

def start():
    subscribe(handle_event)
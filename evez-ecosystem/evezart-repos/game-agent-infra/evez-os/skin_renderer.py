"""
skin_renderer.py — EVEZ-OS Gen 3 Skin API
Renders OS state through a skin.json layer.

Players can design their OS from within (self-programming)
or outside (marketplace skins).
"""

import json
from typing import Optional

class SkinRenderer:
    def __init__(self, skin: dict):
        self.skin = skin
        self.name = skin.get("name", "unnamed")
        self.version = skin.get("version", "0.1.0")

    @classmethod
    def from_file(cls, path: str) -> "SkinRenderer":
        with open(path) as f:
            return cls(json.load(f))

    def render_hud(self, state: dict) -> str:
        s = state.get("state_b", state)
        branch = "FIRE" if s.get("fire") else "NO_FIRE"
        style = self.skin.get("branch_styles", {}).get(branch, {})
        icon = style.get("icon", "·")
        hud_template = self.skin.get("hud_template",
            "{icon} R{round_k} N={N} poly_c={poly_c:.6f} {branch} V={V_new:.6f}")
        try:
            line = hud_template.format(
                icon=icon, round_k=s.get("round_k", "?"),
                N=s.get("N", "?"), poly_c=s.get("poly_c", 0),
                branch=branch, V_new=s.get("V_new", 0),
                ceiling_tick=s.get("ceiling_tick", "?"),
            )
        except Exception:
            line = f"{icon} R{s.get('round_k')} {branch} V={s.get('V_new')}"
        return line

    def render_card(self, state: dict) -> dict:
        s = state.get("state_b", state)
        branch = "FIRE" if s.get("fire") else "NO_FIRE"
        style = self.skin.get("branch_styles", {}).get(branch, {})
        epoch_info = state.get("epoch", {})
        return {
            "skin": self.name, "round": s.get("round_k"), "N": s.get("N"),
            "poly_c": s.get("poly_c"), "fire": s.get("fire"), "V_new": s.get("V_new"),
            "branch": branch, "icon": style.get("icon", "·"),
            "color": style.get("color", "#ffffff"), "label": style.get("label", branch),
            "epoch_name": epoch_info.get("console", ""),
            "epoch_counter": epoch_info.get("evez_counter", ""),
            "tokens": state.get("output", {}).get("tokens", []),
        }

    def render_console_war_badge(self, epoch: dict) -> str:
        badges = self.skin.get("epoch_badges", {})
        epoch_id = str(epoch.get("epoch", 0))
        badge = badges.get(epoch_id, {"label": epoch.get("console", "?"), "icon": "🎮"})
        return f"{badge['icon']} Epoch {epoch_id}: {badge['label']}"

    def render_v_bar(self, V: float) -> str:
        cfg = self.skin.get("v_bar", {})
        ceiling = cfg.get("ceiling", 6.0)
        width = cfg.get("width", 40)
        fill = cfg.get("fill_char", "█")
        empty = cfg.get("empty_char", "░")
        pct = min(V / ceiling, 1.0)
        filled = int(pct * width)
        bar = fill * filled + empty * (width - filled)
        return f"[{bar}] {V:.6f}/{ceiling:.1f} ({100*pct:.2f}%)"


if __name__ == "__main__":
    import json
    skin = json.load(open("workspace/default.skin.json"))
    renderer = SkinRenderer(skin)
    test_state = {
        "state_b": {
            "N": 120, "round_k": 168, "poly_c": 0.789274,
            "fire": True, "V_new": 5.555132, "ceiling_tick": 86
        },
        "output": {"tokens": ["FIRE_EVENT", "SPINE_COMMIT", "TWEET_TOKEN"]},
        "epoch": {"epoch": 6, "console": "Dreamcast",
                  "evez_counter": "cloudflare_DO_waits_for_infra_readiness"}
    }
    print(renderer.render_hud(test_state))
    print(renderer.render_v_bar(5.555132))
    print(renderer.render_console_war_badge(test_state["epoch"]))
    print("skin_renderer.py SELF-TEST PASSED")

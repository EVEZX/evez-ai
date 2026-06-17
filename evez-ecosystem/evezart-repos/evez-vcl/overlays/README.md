# NPC Witness Board — OBS Browser Source Setup

Live threat overlay for EVEZ-OS YouTube RTMP livestreams.

## OBS Setup

1. In OBS, add a **Browser Source** to your scene
2. Set URL to: `https://evezart.github.io/evez-vcl/overlays/npc-witness-board.html`
3. Width: `360` | Height: `700`
4. Enable **"Shutdown source when not visible"** and **"Refresh browser when scene becomes active"**
5. CSS override (for transparent BG): `body { background-color: rgba(0, 0, 0, 0); }`

## Data Source

Fetches from `https://evezart.github.io/witness-registry/api/entities.json` every **60 seconds**.

## Entity Schema

```json
{
  "codename": "IRON_REAPER_7",
  "archetype": "APT",
  "confidence": 0.91,
  "country_code": "RU",
  "ip": "185.220.101.1",
  "behavior": "Systematic port scan 22/80/443, no payload"
}
```

## Archetypes & Icons

| Archetype | Icon | Threat Logic |
|-----------|------|--------------|
| APT | 🎯 | CRITICAL if conf ≥ 0.65 |
| EXFIL | 📤 | CRITICAL if conf ≥ 0.65 |
| C2 | 📡 | CRITICAL if conf ≥ 0.65 |
| BRUTE | 💥 | HIGH if conf ≥ 0.75 |
| SCANNER | 🔍 | MEDIUM/LOW |
| BOT | 🤖 | MEDIUM/LOW |
| RECON | 👁️ | MEDIUM/LOW |
| CRAWLER | 🕷️ | LOW |

CRITICAL entities pulse red; HIGH entities glow orange.

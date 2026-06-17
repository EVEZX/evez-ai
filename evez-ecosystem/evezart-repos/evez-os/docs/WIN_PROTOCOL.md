# WIN PROTOCOL — Self‑Cartography Is the Only Ending

This project "wins" when the system can **trace itself**, **prove its own routing**, and **survive its own narrative**.

In practice, the win condition is: the player’s constructed map matches the recorded pathway traces across three truth‑planes:

- Public Internet (DNS/BGP/TLS/CDN)
- Game backend (matchmaking/auth/state/WebSockets/rollback)
- Mixed reality (public internet artifacts impersonating backend failures, and vice versa)

## The rule that kills delusion

A statement is not allowed to become *canon* unless it carries:

- **Provenance** (where it came from)
- **A falsifier** (what would prove it wrong)
- **A trace** (what was observed, from what vantage)

Everything else is *pending*. Pending is not shame; pending is honesty.

## Minimal "winning" run

1) Initialize the immutable spines:

- `python tools/evez.py init`
- `python tools/evez.py arg-init`

2) Run one incident cycle and record it to the spine:

- `python tools/evez.py cycle --ring 3 --anomaly "conflicting truth planes" --hypothesis "DNS split" --probe "compare resolver outputs" --result "NXDOMAIN on Wi-Fi only" --omega "two-vantage discipline"`

3) Drop an ARG narration fragment that references the *same* evidence (but does not overwrite it):

- `python tools/evez.py arg-drop --lobby DNS --lens "resolver split" --payload "Wi-Fi NXDOMAIN, LTE OK. Pending until authoritative check."`

4) Generate the self-cartography map:

- `python tools/self_cartography.py`

If you can reproduce the same diagnosis from a different vantage and the map still holds, you’re not roleplaying. You’re winning.

## Shipping to GitHub (what "done" looks like)

- Repo runs from a clean checkout.
- Spines are append-only.
- Docs explain pending vs final.
- A small demo run produces both a spine and a rendered map.

If you feel like you “won” without a trace, you didn’t win—you narrated.

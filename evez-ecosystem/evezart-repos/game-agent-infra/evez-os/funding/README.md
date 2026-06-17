# Funding Assets — Spine-driven, provable, replayable

This module is **not** “a deck folder.” It is a *truth-plane interface* for fundraising.

Principle: **Investor-facing materials are projections.** Your numbers and claims live in an append-only spine.
Anything that can’t be traced back to a source (or a stated assumption) is **pending** and must be labeled.

If you want to “win,” you do it the same way as the rest of this repo:
immutability + rebuildable views + falsifiers.

## Currency discipline ("summon currency ≠ invent it")

Any money figure that crosses currencies must be anchored to an immutable FX snapshot.
Snapshots are retrieved from the **European Central Bank (ECB) euro reference exchange rate feed** and stored in:

- `funding/data_room/FX-YYYY-MM-DD-BASE.json`

Create a snapshot (and optionally append it as an `asset` entry to `spine/FUNDING_SPINE.jsonl`):

```bash
python tools/evez.py fx-snapshot --base USD --symbols EUR,USD,GBP,JPY --append-spine
```

Source of truth: ECB daily XML feed used by the tool:
`https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml`


## Cheats (dev/test only)

To simulate funding flows safely, mint only test currency and always append a spine record.

```bash
export EVEZ_ENV=dev
python tools/evez.py cheat deposit --currency USD_TEST --amount 50000 --append-spine --memo "scenario test"
python tools/evez.py cheat inf --currency USD_TEST --amount 1000000000 --append-spine
python tools/evez.py cheat reset --currency USD_TEST --append-spine
```

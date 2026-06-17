# EVEZ-OS State Coupling Architecture

From Steven's state machine diagram, 2026-02-24:

```
[Legacy Systems / Consoles]
  ├─ Xbox     (Gen 9: specs without exclusives)
  ├─ GameCube (Gen 5: back old strength, miss new dimension)
  ├─ N64      (Gen 4: fragmentation kills everything)
  ├─ SNES/DS  (Gen 3: blast processing lie)
  └─ GameBoy  (Gen 1: no save state)
          │
          ▼
[Dashboard / Graphics Abstraction]  ← SkinRenderer (skin.json layer)
          │
          ▼
[State A] + [State B]
State A = user fork instance (EVEZFork)
State B = canonical spine (EVEZCore, GitHub-committed)
     │        │
     └──(exchange/coupling)──┘
       ValidatorBus delta gate
       |poly_c_A - poly_c_B| < 0.001
               │
               ▼
        [Composed State]
        truth_plane = CANONICAL | DIVERGED
          /         \
         ▼           ▼
   [Branch Path 1]  [Branch Path 2]
   FIRE             NO FIRE
   poly_c >= 0.500  poly_c < 0.500
         \           /
          ▼         ▼
           [Output Node]
           spine/watch_composite_N.py
               │
           [Tokens/Events]
           FIRE_EVENT | STATE_ADVANCE
           SPINE_COMMIT | TWEET_TOKEN
               │
        (feedback / loopback)
               └──────────► upstream
                            launch_next_probe
```

## Component Mapping

| Diagram Node | EVEZ-OS Component |
|---|---|
| Legacy Systems | Console war training epochs (9 pathologies) |
| Dashboard / Graphics Abstraction | SkinRenderer + skin.json |
| State A | EVEZFork (per-user instance) |
| State B | EVEZCore canonical (GitHub spine) |
| Exchange/coupling | ValidatorBus delta gate |
| Composed State | truth_plane (CANONICAL / DIVERGED) |
| Branch Path 1 | FIRE → spine commit + tweet |
| Branch Path 2 | NO FIRE → state advance |
| Output Node | watch_composite_N.py + hyperloop_state.json |
| Tokens/Events | FIRE_EVENT, SPINE_COMMIT, TWEET_TOKEN, STATE_ADVANCE |
| Feedback/loopback | Next round probe (Hyperbrowser task) |

## Console War Epoch → State Machine Failure Mapping

| Epoch | Console | State Machine Failure | EVEZ-OS Counter |
|---|---|---|---|
| 0 | Pong | No State B | evez_core_runs_any_N |
| 1 | Atari | No save state = no checkpoints | spine_immutability_never_resets |
| 2 | NES | Spec war over software = no coupling | each_commit_permanent_IP |
| 3 | SNES/Genesis | Fake poly_c (blast processing lie) | validator_bus_delta_gate |
| 4 | 3DO/Jaguar | Fragmented State B = multiple canonical | one_canonical_AGPL_fork |
| 5 | PS1/Saturn | No pluggable reality modules | pluggable_reality_modules |
| 6 | Dreamcast | Correct coupling, wrong epoch | cloudflare_DO_waits_for_infra_readiness |
| 7 | Wii | Blue ocean = no feedback loop | hyperloop_never_stops |
| 8 | Wii U | Identity crisis = State B unclear | evez_os_identity_IS_the_math |
| 9 | Xbox/PS5 | Specs without exclusives = no Output Node | spine_commits_are_the_exclusives |

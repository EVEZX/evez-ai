## Genre lock
Read `docs/GENRE_LOCK_ROLLBACK_SHOOTER.md` first. This narration assumes **rollback shooter** timing + truth contracts.

# Let’s Play: Admin Walkthrough (developer narration)

You want the “admin view” of the stack? Fine. I built the damn thing. So here is the tour the way it actually behaves when the internet starts lying to your face.

You are standing in three rooms at once:

The public room is **DNS/BGP/TLS/CDN**, the part of the world that pretends “name means address” and “address means reachable” and “reachable means correct.”

The private room is your **matchmaking/auth/state/WebSocket backend**, where you manufacture authority under latency.

The cursed room is **mixed reality**, where public turbulence impersonates your bugs and your bugs impersonate public turbulence.

Now the rule, the one that keeps you alive when everything is on fire:

The log is the truth. The view is a costume. If you rewrite the truth, you are not debugging—you are cosplaying.

So we start by booting the spine. Not because it is sexy. Because without it you will swear you “fixed” something when you just changed what you were looking at.

```bash
python tools/evez.py init
```

Now I want you to do the first sinful thing on purpose: ship a confident story with zero proof. Say it is DNS. Say it is BGP. Say it is the server. Feel how good it feels to be done.

And now—good—now we crush that feeling, because that feeling is how you lose.

We run an FSC cycle. We name the anomaly in ugly, specific terms. We do not write poetry. We write a failure signature.

```bash
python tools/evez.py cycle --ring R4 --anomaly "players see hits, server corrects to misses under jitter" \
  --latency "inject 150ms jitter" --tighten "reduce client buffer" \
  --provenance "trace:otel" "match:42" "netem:jitter"
```

That appends one immutable record. One. No edits. No retroactive ego saves.

Now generate the diagram.

```bash
python tools/evez.py diagram
```

At this point you will want to lie to yourself again. You will want to say “the diagram proves it.” It does not. The diagram is a flashlight, not a verdict.

So you walk into the **Internet X-Ray** room and you fire probes at the public stack. Cross-resolver DNS. Cross-vantage routes. TLS chain checks. CDN stale-serve detection. Not because you are paranoid. Because the internet is a distributed hallucination machine and you do not get to diagnose from a single eyeball.

If the probes disagree by region, you are in the public lobby.

If the probes agree but the game still diverges, you are in the backend lobby.

If the probes flicker and the backend flickers, welcome to mixed reality—you are going to earn your pay today.

Now the “retrocausal” part, the part you actually came here for.

The client predicts.
The server finalizes.
Rollback rewrites perception.

If you try to eliminate rollback, you will either make the game feel like sludge or you will start lying harder. Pick your poison.

So instead, you do the grown-up thing: you tag the truth-plane.

Pending state is allowed to be wrong.
Final state must be right.
Every correction carries provenance so the player’s experience can be explained instead of gaslit.

And if you want the patch, it is sitting in:

`services/game-server/netcode_patch/`

Now go ahead and feel the second forbidden impulse: the impulse to declare yourself “above bias.”

You are not.
Your metrics are not.
Your reward loops are not.

So you install the bias constitution in `docs/constitution/` and you treat it like a production contract: what you optimize, what you refuse to optimize, and how you audit drift.

That is the whole tour.

Not magic. Not mysticism.
Just ruthless provenance, layered truth, and a spine that remembers what you did when you want to pretend you did not.

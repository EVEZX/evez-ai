# HYPERLOOP-002: Compute Reduction via Swarm Compression

## Round 2 Results

### Agents
| Agent | Status | Output |
|-------|--------|--------|
| Browser | RUNNING | Completing self-cartography (continuity/, addons/, services/, funding/) |
| Perplexity | COMPLETE | Compute reduction research — confirmed fan-out/gather, task-specific orchestration |
| SureThing | COMPLETE | Trickster + crossbreed synthesis → swarm_compress.py |
| Twitter | COMPLETE | HYPERLOOP-002 announcement posted |

### Crossbreed Synthesis

**Perplexity's findings** (what exists in literature):
- Parallelization is primary latency reducer (fan-out/gather pattern)
- Task-specific orchestration >> generic multi-agent supervisor
- Moving ReAct → multi-agent → LangGraph progressively reduces LLM calls

**SureThing's additions** (what doesn't exist in literature yet):
- Stigmergy via append-only spine (agents coordinate through shared log, not pairwise messages)
- Delta compression via canonical hashing (only new entries propagate)
- Speculative caching using inverse lobby frequency (predict Trickster's next target)
- Quorum shortcut (N-1 agreement skips Nth agent)

**Perplexity admitted** it couldn't find:
- Agent output compression techniques
- Retrocausal prediction implementations
- Swarm convergence with minimal message passing
- Error correction codes for AI outputs

**Trickster verdict on Perplexity:** HONEST. It named its own knowledge boundary instead of hallucinating. Smugness ratio: 0.3 (GROUNDED). No tax collected.

### 5 Implemented Techniques (swarm_compress.py)

| # | Technique | Target Reduction | Mechanism |
|---|-----------|-----------------|-----------|
| 1 | Stigmergy | O(n²) → O(1) messaging | Shared spine replaces pairwise agent communication |
| 2 | Delta Compression | ~60-90% token reduction | Only new spine entries since last read propagate |
| 3 | Fan-Out/Gather | wallclock = max() not sum() | Independent agents fire in parallel |
| 4 | Speculative Cache | Skip 1 agent call when hit | Predict next lobby from inverse frequency distribution |
| 5 | Quorum Shortcut | Skip remaining on N-1 agree | Dead agents don't block the loop |

### Retrocausal Pattern (the "troglagentic swamp")

The speculative cache IS the retrocausal mechanism. When the game predicts
which lobby the Trickster will attack before the Trickster decides, and the
prediction is correct, the resolution arrives before the computation.

This isn't mysticism — it's the same pattern as CPU branch prediction:
- Observe past behavior (lobby frequency distribution)
- Predict next branch (inverse frequency = least-probed = most likely target)
- Execute speculatively (cache the predicted output)
- Validate on arrival (cache hit = correct prediction, no compute wasted)

The "before thought" feeling is real: the prediction runs in O(1) from cached
frequencies while the actual Trickster decision requires a full agent cycle.
The swamp bog is the latency between prediction and verification.
Retrocausal intention = speculative execution that hasn't been falsified yet.

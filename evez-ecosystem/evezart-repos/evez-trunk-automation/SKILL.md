# EVEZ Trunk Automation

Autonomous branch decomposition and execution. Send any objective, get back compressed trunk state.

## Input

```json
{
  "objective": "string"
}
```

## Output

```json
{
  "branches": [{"id": "recon", "role": "recon", ...}],
  "surviving_logic": [],
  "compression_timestamp": "ISO timestamp"
}
```

## Usage

```python
from trunk_automation import TrunkAutomation
trunk = TrunkAutomation()
result = trunk.decompose_and_execute("Build something")
```

## Branch Sequence

1. **Recon** (Perplexity) — gather evidence
2. **Skeptic** (ChatGPT) — challenge logic
3. **Architect** (Claude) — refactor structure
4. **Executor** (Base44) — route to behavior

Built by EVEZ-ART | EVEZ Sensory Engine
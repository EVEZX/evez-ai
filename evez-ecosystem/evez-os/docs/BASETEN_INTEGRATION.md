# EVEZ-OS INFRASTRUCTURE NOTES
## Baseten Integration (2026-02-24)

**Status:** AWAITING_KEY_ROTATION

Env vars added to `evez-autonomizer` Vercel project:
- `BASETEN_BASE_URL` = `https://inference.baseten.co/v1` (production/preview/development)
- `BASETEN_MODEL` = `openai/gpt-oss-120b` (production/preview/development)
- `BASETEN_API_KEY` = **PENDING** — Steven must rotate at app.baseten.co/settings/api-keys and paste new key

**Usage pattern (OpenAI-compatible drop-in):**
```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["BASETEN_API_KEY"],
    base_url=os.environ["BASETEN_BASE_URL"]  # https://inference.baseten.co/v1
)

response = client.chat.completions.create(
    model=os.environ["BASETEN_MODEL"],  # openai/gpt-oss-120b
    messages=[{"role": "user", "content": prompt}],
    stream=True
)
```

**Gap routing:** Use Baseten for high-context synthesis tasks where gpt-oss-120b quality exceeds Groq llama-3.3-70b.
Groq remains default inference layer. Baseten = overflow / specialized.

## R176 + R177 State (2026-02-24)

| Round | N | poly_c | Fire | V | Ceiling |
|-------|---|--------|------|---|--------|
| R176 | 128=2^7 | 0.504249 | FIRE#29 | 5.847568 | x94 |
| R177 | 129=3x43 | 0.441000 | NO FIRE | 5.882836 | x95 |

Est ceiling: R178 N=130=2x5x13 (FIRE#30 est, CTC est_ceiling_round=178)
V progress: 98.05% of V_v2=6.0

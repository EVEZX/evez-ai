---
name: evez-fire-engine
version: 0.2.0
description: FIRE event scorer and spine logger. Computes poly_c, applies SC normalization, logs to PostgreSQL and GitHub lord-evez666.
tags: [evez, fire, poly_c, cpf, spine]
---

# EVEZ FIRE Engine

Scores events against the CPF formula, applies supercritical normalization, logs to the spine.

## Usage in session

```
/fire The KoPE paper independently derived the CPF formula from neuroscience.

→ Enter τ (depth across time): 22
→ Enter ω (independent confirmations): 3.8
→ Enter topo (0.0-1.0): 1.0
→ Enter N (independent lenses): 8

poly_c_raw = 22 × 3.8 × 1.0 / (2√8) = 14.77
poly_c_SC  = 14.77 / (1 + 14.77) = 0.937  ← SUPERCRITICAL
status: CANONICAL | regime: CRITICAL_MASS

→ Log to spine? [Y/n]: Y
→ ✓ Logged. Hash: kope_cpf_bridge_2026
```

## Direct execution

```bash
python run.py \
  --title "KoPE → CPF Phase Dynamics" \
  --domain physics_cognition \
  --tau 22 --omega 3.8 --topo 1.0 --N 8 \
  --falsifier "If KoPE formula cannot algebraically transform to CPF"
```

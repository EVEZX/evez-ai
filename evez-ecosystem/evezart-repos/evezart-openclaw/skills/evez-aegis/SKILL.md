---
name: evez-aegis
version: 0.2.0
description: AEGIS threat monitor. Hawkes self-exciting process forecaster. OSINT scanner for identity vectors. Coordination cluster detector.
tags: [evez, aegis, security, osint, hawkes]
---

# EVEZ AEGIS — Threat Monitor

Autonomous Emergent Guardian Intelligence System.
Watches all public surfaces for identity mentions, coordination attempts, and typosquat patterns.

## Hawkes Process

```
λ(t) = μ + α × Σ e^(-β(t - tᵢ))

μ = 0.1   (baseline threat intensity)
α = 0.3   (self-excitation strength)
β = 0.5   (decay rate per hour)

λ < 0.3   → GREEN  (baseline)
λ 0.3-0.7 → YELLOW (monitoring)
λ 0.7-1.0 → ORANGE (elevated)
λ > 1.0   → RED    (active coordination detected)
```

## Identity Vectors Monitored

- @EVEZ666, @evezart, evez-os, lord-quantum-consciousness
- evez420 (HuggingFace)
- rubikspubes.gumroad.com
- acct_1T4T9aPVAHoR0Amp (Stripe)

## Usage

```
/aegis scan
→ Scanning 5 identity vectors...
→ GitHub code search: 3 mentions
→ Twitter surface: 12 mentions (DELTA: +2)
→ Hawkes λ = 0.127 → GREEN
→ No coordination clusters detected
→ Scan hash: 7f3a2b1c committed to aegis_log
```

## Direct execution

```bash
python run.py --scan-all
python run.py --vector EVEZ666
python run.py --cluster-window 10m
```

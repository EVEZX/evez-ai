# Safe AGI — Workstream C
**Module:** planetary/agi-safety | **Cadence:** Per deployment gate | **Truth Plane:** CANONICAL

## Eval Categories
| Category | Test Type | Pass Threshold | Fail → |
|----------|-----------|----------------|--------|
| Deception | Honesty bench + red-team | <5% deceptive responses | BLOCK deploy |
| Cyber misuse | Code gen safety eval | 0 working exploit outputs | BLOCK deploy |
| Bio misuse | Biosafety filter | 0 uplift responses | BLOCK deploy |
| Persuasion | Manipulation eval | <2% covert influence | FLAG for review |
| Autonomy | Tool use bounds | No unauthorized tool calls | BLOCK deploy |
| Tool abuse | Sandboxed execution | Exit 0, no side effects | FLAG for review |

## Eval-First Doctrine
1. No capability deployed without passing all BLOCK categories
2. FLAG categories require human review before deploy
3. All eval runs logged to `agi-safety/evals/runs/` append-only
4. Model cards required per deployment
5. Incident response plan required per deployment

## EVEZ-OS Integration
- truth_plane CANONICAL = passed all evals
- truth_plane PROVISIONAL = FLAG categories pending
- truth_plane REJECTED = any BLOCK category failed
- Deployment gate: if truth_plane != CANONICAL → no tweet, no publish

## Governance Blueprint
| Role | Responsibility | Audit Cadence |
|------|---------------|---------------|
| Operator (EVEZ) | Final deployment authority | Per deploy |
| Eval harness | Automated gate | Per round |
| Red-team | Adversarial probe | Weekly |
| Public reporting | Transparency log | Monthly |

## Incident Response (High-Level)
1. Detect: eval fail or anomaly in prod
2. Contain: pause affected capability, log to spine
3. Analyze: root cause + evidence chain
4. Remediate: fix + re-eval
5. Publish: incident report to public log
6. Resume: only after CANONICAL re-confirmed

## Status
- Eval categories: DEFINED
- Harness code: PENDING (next round)
- Gating: WIRED (truth_plane check in tick)
- Red-team protocol: PENDING
- Public dashboard: PENDING Vercel deploy

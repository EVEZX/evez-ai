# Revenue Engine Skill - RUNBOOK

## Quick Start

```bash
# Clone or copy this skill to your project
cp -r revenue-engine-skill/ /your/workspace/

# Test it
cd revenue-engine-skill
python3 revenue_engine.py --channel x --action post --content "Testing EVEZ Revenue Engine!"
```

## Setup Checklist

- [ ] Copy `revenue_engine.py` to your project
- [ ] Ensure `evez-outreach/` directory exists with templates
- [ ] Test: `python3 revenue_engine.py --channel status`
- [ ] Configure desired channel (Fiverr, X, etc.)

## Observable Metrics

### For Phenomenology Tracking

**Track: Skill Chain Reaction**
- Log skill_published events in LEDGER.md with repo_source field
- Compare: First skill publish vs. 5th skill publish on ClawHub

**Commands to verify:**
```bash
# Check skill published
grep "skill_published" LEDGER.md

# Count skills from evez-os
grep -c "evez-os" _meta.json
```

### Automation Integration

**GitHub Actions (optional):**
```yaml
# .github/workflows/revenue.yml
name: Revenue Engine
on: [push]
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: python3 revenue_engine.py --channel status
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "No template found" | Create `evez-outreach/{template-name}.md` |
| Import error | Ensure `context.bridge` available or remove import |
| File permission | Run with write access to workspace |

## Notes

- All actions are "draft mode" — require manual posting to actual platforms
- Context bridge logs to `revenue_log.jsonl` in workspace root
- Extend by adding new channels in `RevenueEngine` class
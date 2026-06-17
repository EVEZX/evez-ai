# Revenue Engine Skill

A plug-and-play revenue execution module for AI agents. Execute revenue-generating actions across multiple channels (Fiverr, Consulting, X/Twitter) with structured logging and context bridging.

## What It Does

- **Fiverr Integration**: Load and prepare gig templates for posting
- **Consulting DM**: Generate and prepare outreach messages
- **X/Twitter Posting**: Create and prepare content for social distribution
- **Context Bridge**: Logs all revenue actions to a unified ledger for decision tracking

## Installation

```bash
cd your-project
pip install -r requirements.txt
```

## Usage

```python
from revenue_engine import RevenueEngine

engine = RevenueEngine()

# Post to Fiverr (draft mode)
result = engine.post_fiverr_gig()

# Send consulting DM
result = engine.send_consulting_dm("@target", "Your custom message")

# Post to X
result = engine.post_to_x("Your post content")

# Get status
status = engine.get_revenue_status()
```

## CLI

```bash
python3 revenue_engine.py --channel fiverr --action post
python3 revenue_engine.py --channel x --action post --content "Hello world"
python3 revenue_engine.py --channel consulting --action dm --target @prospect
```

## Output Format

All actions return:
```json
{
  "success": true,
  "status": "ready_for_post|ready_for_send",
  "action_needed": "Manual: copy to Fiverr..."
}
```

## Requirements

- Python 3.8+
- pathlib (stdlib)
- json (stdlib)

## Context Bridge

If `context.bridge` is available in your environment, revenue actions are automatically logged to the decision context. Otherwise, falls back to file-only logging.

## License

MIT - Modify freely for your revenue ops.
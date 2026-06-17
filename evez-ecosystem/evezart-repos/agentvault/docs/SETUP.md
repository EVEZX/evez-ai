# Setup

This repo is designed so you can run it locally **or** via GitHub Actions.

## 1) Put your exports in the vault

### ChatGPT

Use the official export flow to download your data export zip. Extract it and copy either:

- `chat.html` (supported), and/or
- any `conversations.json` file if present (supported when available)

into:

- `vault/chatgpt/` (create the folder if needed)

### Perplexity

Export important Threads as **Markdown** if possible, or copy/paste to `.md` files.

Place them into:

- `vault/perplexity/`

## 2) Run locally (recommended first)

Requirements: Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python index/build_index.py
python agent/run.py --query "what did we decide about the agent runtime?"
```

## 3) GitHub Actions nightly run

A workflow at `.github/workflows/nightly.yml` runs the index build nightly.

If you later want the workflow to call an LLM (Perplexity/OpenAI/etc.), add secrets in repo settings.
Do not paste keys into issues.

## Data notes

The index is stored in `data/agentvault.sqlite`.
By default this file is NOT committed.

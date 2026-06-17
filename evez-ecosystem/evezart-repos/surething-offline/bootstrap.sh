#!/usr/bin/env bash
# SureThing Offline — One-line bootstrap
set -euo pipefail

echo ""
echo "\u256c SureThing Offline — Bootstrap"
echo ""

if ! command -v python3 &>/dev/null; then echo "\u2717 Python3 not found"; exit 1; fi
echo "\u2713 Python $(python3 --version)"

if ! command -v ollama &>/dev/null; then
  echo "\u2192 Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "\u2713 Ollama installed"
fi

MODEL=${OLLAMA_MODEL:-mistral}
echo "\u2192 Pulling $MODEL..."
ollama pull "$MODEL" || echo "  (start ollama first: ollama serve)"

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env
mkdir -p data/chroma data/drafts

echo ""
echo "\u2713 Ready. Starting SureThing Offline at http://localhost:${PORT:-8420}"
echo ""

pgrep -x ollama > /dev/null || (ollama serve &>/tmp/ollama.log & sleep 2)
python run.py

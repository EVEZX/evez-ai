#!/usr/bin/env bash
set -euo pipefail

# 1. Ensure required tools are installed
if ! command -v git >/dev/null; then echo "git not found"; exit 1; fi
if ! command -v pnpm >/dev/null; then echo "pnpm not found"; exit 1; fi
if ! command -v node >/dev/null; then echo "node not found"; exit 1; fi

# 2. Clone OpenClaw repository (if not already)
if [ ! -d "openclaw" ]; then
  git clone https://github.com/openclaw/openclaw.git
fi
cd openclaw

# 3. Install dependencies
pnpm install

# 4. Restore workspace backup (replace existing workspace)
if [ -f "../backup.tar.gz" ]; then
  tar -xzf "../backup.tar.gz" -C "../"
else
  echo "Backup file not found. Ensure backup.tar.gz is in the parent directory."
  exit 1
fi

# 5. Start OpenClaw gateway (adjust port if needed)
openclaw gateway start

# 6. Optional: Run initial tests
# openclaw config validate

# 7. Keep container running
exec "$@"

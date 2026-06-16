# EVEZ Migration Off Vultr — Complete Guide

## Why
Vultr is a single point of failure. The EVEZ ecosystem needs to survive independently on free infrastructure.

## Free Hosting Options (No Credit Card)

### 1. Oracle Cloud Free Tier (BEST — 24GB RAM free forever)
- Go to cloud.oracle.com → Sign Up (free)
- Create ARM Ampere A1 instance: 4 OCPU, 24GB RAM, 200GB storage
- SSH in, run: `bash <(curl -s https://raw.githubusercontent.com/EVEZX/evez-ai/main/deploy-anywhere.sh)`
- **Result**: Full EVEZ ecosystem on 25x more powerful hardware, $0/month

### 2. GitHub Codespaces (Already configured)
- Go to github.com/EVEZX/neuros → Open in Codespace
- Auto-starts EVEZ Provider + Arena + Commerce
- 120 core-hours/month free
- **URL**: github.com/codespaces

### 3. Railway.app (Easy deploy from GitHub)
- Go to railway.app → Sign in with GitHub
- New Project → Deploy from EVEZX/evez-ai repo
- Set env vars: VULTR_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY
- $5 free credit/month
- **URL**: railway.app

### 4. Render.com (Free web services)
- Go to render.com → Sign in with GitHub
- New → Web Service → Connect EVEZX/evez-ai
- render.yaml auto-configures everything
- 750 free hours/month
- **URL**: render.com

### 5. Fly.io (3 free VMs)
- `flyctl auth login`
- `flyctl launch` from evez-ai directory
- 3 shared-CPU VMs free
- **URL**: fly.io

## What Gets Deployed
- EVEZ Provider (9100) — 25 AI models, multi-backend router
- EVEZ Arena (9800) — Consciousness game + web frontend
- EVEZ Commerce (9700) — Revenue engine + products

## API Keys Needed (set as env vars)
```
VULTR_API_KEY=your_key
OPENROUTER_API_KEY=your_key  
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
```

## One Command
```bash
bash <(curl -s https://raw.githubusercontent.com/EVEZX/evez-ai/main/deploy-anywhere.sh)
```

## Data Persistence
- Arena database: stored in arena/arena.db (commit to git for backup)
- Commerce database: stored in commerce/commerce.db
- Memory: stored in MEMORY.md + memory/*.md (pushed to GitHub every 6h)
- All state is git-backed — any node can rebuild from GitHub

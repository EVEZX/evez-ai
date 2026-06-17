FROM myoung34/github-runner:latest

# Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Node 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Common pip packages used by EvezArt workflows
RUN pip install --no-cache-dir \
    requests \
    anthropic \
    python-dateutil \
    feedparser

LABEL org.opencontainers.image.source="https://github.com/EvezArt/evez-autonomous-ledger"
LABEL org.opencontainers.image.description="EvezArt self-hosted GitHub Actions runner"

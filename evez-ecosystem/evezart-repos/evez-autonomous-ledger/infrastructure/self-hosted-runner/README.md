# Self-Hosted GitHub Actions Runner for EvezArt

Eliminates GitHub Actions minutes usage by running workflows on your own hardware.

## Quick Start (VPS / any Linux box)

```bash
export GITHUB_TOKEN=ghp_your_token_here   # needs admin:org scope
./setup.sh EvezArt my-runner-name
```

This downloads the runner, registers it with the EvezArt org, and installs it as a systemd service.

## Docker (recommended for VPS)

```bash
export GITHUB_TOKEN=ghp_your_token_here
docker compose up -d
```

Or build the custom image with pre-installed Python/Node:

```bash
docker build -t evez-runner .
docker compose up -d
```

## Raspberry Pi

1. Use a Pi 4 (4GB+ RAM) with Ubuntu Server 22.04 arm64
2. Clone this directory to the Pi
3. Run `GITHUB_TOKEN=ghp_xxx ./setup.sh`
4. The runner auto-registers with the `self-hosted,linux` labels

## Activating Self-Hosted Runners

Once a runner is registered, set this org-level variable in GitHub:

**Settings → Secrets and variables → Actions → Variables → New variable**

- Name: `RUNNER_LABEL`
- Value: `self-hosted`

All workflows use `${{ vars.RUNNER_LABEL || 'ubuntu-latest' }}`, so they'll automatically use your runner. Remove the variable to fall back to GitHub-hosted runners.

## Managing the Runner

```bash
# Check status (systemd)
sudo ./svc.sh status

# Stop/start
sudo ./svc.sh stop
sudo ./svc.sh start

# Uninstall
sudo ./svc.sh uninstall

# Docker
docker compose logs -f
docker compose down
```

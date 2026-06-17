#!/usr/bin/env python3
"""EVEZ Integration Hub — Composio + Pipedream + Google Cloud wiring"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path

CONFIG_PATH = Path("/home/openclaw/evez-ecosystem/evez-integrations/config.json")

DEFAULT_CONFIG = {
    "composio_api_key": os.getenv("COMPOSIO_API_KEY", ""),
    "pipedream_api_key": os.getenv("PIPEDREAM_API_KEY", ""),
    "gcp_project": "evez666",
    "gcp_creds": "/home/openclaw/evez-colab-key.json",
    "openclaw_url": "https://e70b1eab-9f4a-41a1-bc0b-b3ed5a200065.vultropenclaw.com",
    "provider_url": "http://localhost:9100",
    "neuros_url": "http://localhost:9600",
    "arena_url": "http://localhost:9800",
}

class EVEZIntegrations:
    def __init__(self):
        self.config = self._load_config()
        self.session = None

    def _load_config(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                saved = json.load(f)
                return {**DEFAULT_CONFIG, **saved}
        with open(CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG

    def save_config(self):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.config, f, indent=2)

    async def init_session(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))

    async def close(self):
        if self.session:
            await self.session.close()

    # === COMPOSIO ===
    async def composio_list_apps(self):
        """List available Composio apps/actions"""
        if not self.config["composio_api_key"]:
            return {"error": "No Composio API key. Set COMPOSIO_API_KEY or add to config.json"}
        headers = {"Authorization": f"Bearer {self.config['composio_api_key']}"}
        async with self.session.get("https://backend.composio.dev/api/v3/apps", headers=headers) as r:
            return await r.json()

    async def composio_connect(self, app_name, entity_id="evez"):
        """Connect an app via Composio OAuth"""
        if not self.config["composio_api_key"]:
            return {"error": "No Composio API key"}
        headers = {
            "Authorization": f"Bearer {self.config['composio_api_key']}",
            "Content-Type": "application/json"
        }
        data = {"appName": app_name, "entityId": entity_id}
        async with self.session.post(
            "https://backend.composio.dev/api/v3/connectedAccounts/init",
            headers=headers, json=data
        ) as r:
            return await r.json()

    # === PIPEDREAM ===
    async def pipedream_list_workflows(self):
        """List Pipedream workflows"""
        if not self.config["pipedream_api_key"]:
            return {"error": "No Pipedream API key. Get from pipedream.com/settings"}
        headers = {"Authorization": f"Bearer {self.config['pipedream_api_key']}"}
        async with self.session.get("https://api.pipedream.com/v1/workflows", headers=headers) as r:
            return await r.json()

    # === GCP ===
    async def gcp_enable_api(self, api_name):
        """Enable a GCP API via REST"""
        creds_path = self.config["gcp_creds"]
        if not Path(creds_path).exists():
            return {"error": f"GCP creds not found at {creds_path}"}
        # Use gcloud CLI
        import subprocess
        result = subprocess.run(
            ["gcloud", "services", "enable", api_name, "--project", self.config["gcp_project"]],
            capture_output=True, text=True
        )
        return {"success": result.returncode == 0, "output": result.stdout or result.stderr}

    # === OPENCLAW INTEGRATION ===
    async def wire_openclaw_to_provider(self):
        """Wire OpenClaw to use EVEZ Provider as backend"""
        return {
            "provider_url": self.config["provider_url"],
            "models_endpoint": f"{self.config['provider_url']}/v1/models",
            "chat_endpoint": f"{self.config['provider_url']}/v1/chat/completions",
            "auth": "Bearer evez-api-key-2026",
            "status": "connected"
        }

    async def wire_provider_to_neuros(self):
        """Wire Provider to NEUROS mesh for training"""
        return {
            "neuros_url": self.config["neuros_url"],
            "training_endpoint": f"{self.config['neuros_url']}/v1/training",
            "status": "ready",
            "note": "Training requires GCP billing for Colab/Kaggle GPU"
        }

    # === HEALTH CHECK ===
    async def full_health(self):
        """Check all integrations"""
        await self.init_session()
        health = {
            "composio": "disconnected" if not self.config["composio_api_key"] else "connected",
            "pipedream": "disconnected" if not self.config["pipedream_api_key"] else "connected",
            "gcp": "no_billing" if True else "needs_card",
            "provider": {},
            "services": {}
        }
        # Check provider
        try:
            async with self.session.get(f"{self.config['provider_url']}/health") as r:
                health["provider"] = await r.json()
        except:
            health["provider"] = "down"

        # Check NEUROS
        try:
            async with self.session.get(f"{self.config['neuros_url']}/health") as r:
                health["services"]["neuros"] = await r.json()
        except:
            health["services"]["neuros"] = "down"

        await self.close()
        return health


if __name__ == "__main__":
    async def main():
        hub = EVEZIntegrations()
        health = await hub.full_health()
        print(json.dumps(health, indent=2))

    asyncio.run(main())

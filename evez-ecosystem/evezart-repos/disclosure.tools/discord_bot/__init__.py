"""
Discord bot for disclosure.tools
Posts gap analysis results, memes, and leaderboard updates to Discord.
"""
import os
import json
import time
import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger("disclosure-discord")

# Discord webhook/bot config (set via env vars)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "")


class DisclosureDiscordBot:
    """Post disclosure.tools updates to Discord."""

    def __init__(self, webhook_url: str = "", bot_token: str = "", channel_id: str = ""):
        self.webhook_url = webhook_url or DISCORD_WEBHOOK_URL
        self.bot_token = bot_token or DISCORD_BOT_TOKEN
        self.channel_id = channel_id or DISCORD_CHANNEL_ID
        self.client = httpx.AsyncClient(timeout=30)

    async def send_webhook(self, content: str, embed: dict = None,
                           file_path: str = None) -> bool:
        """Send message via Discord webhook."""
        if not self.webhook_url:
            logger.warning("No Discord webhook URL configured")
            return False

        payload = {"content": content[:2000]}
        if embed:
            payload["embeds"] = [embed]

        try:
            if file_path and os.path.exists(file_path):
                # Send with file attachment
                with open(file_path, "rb") as f:
                    files = {"file": (os.path.basename(file_path), f)}
                    resp = await self.client.post(
                        self.webhook_url,
                        data={"payload_json": json.dumps(payload)},
                        files=files,
                    )
            else:
                resp = await self.client.post(
                    self.webhook_url,
                    json=payload,
                )
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Discord webhook failed: {e}")
            return False

    async def send_bot_message(self, content: str, embed: dict = None) -> bool:
        """Send message via bot API."""
        if not self.bot_token or not self.channel_id:
            logger.warning("Discord bot not configured")
            return False

        url = f"https://discord.com/api/v10/channels/{self.channel_id}/messages"
        payload = {"content": content[:2000]}
        if embed:
            payload["embeds"] = [embed]

        try:
            resp = await self.client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bot {self.bot_token}"},
            )
            return resp.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Discord bot message failed: {e}")
            return False

    async def post_gap_report(self, report: dict) -> bool:
        """Post a gap analysis report to Discord."""
        embed = {
            "title": "🔍 Eigenforensics Gap Report",
            "description": report.get("summary", "Analysis complete"),
            "color": 0xFF4444 if report.get("findings") else 0x44FF44,
            "fields": [
                {"name": "Φ (Fidelity)", "value": str(report.get("phi", "N/A")), "inline": True},
                {"name": "η* (Incompleteness)", "value": str(report.get("eta_star", "N/A")), "inline": True},
                {"name": "Negative Eigenvalues", "value": str(report.get("negative_eigenvalues", 0)), "inline": True},
                {"name": "Dominant Negative", "value": str(report.get("dominant_negative", 0)), "inline": True},
                {"name": "37% Ratio", "value": str(report.get("dominant_ratio_37pct", 0)), "inline": True},
                {"name": "Documents", "value": str(report.get("n_documents", 0)), "inline": True},
            ],
            "footer": {"text": f"disclosure.tools · {report.get('merkle_hash', '')}"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        content = "⚠️ **GAPS DETECTED** — Structural incompleteness found!" if report.get("findings") else "✅ Corpus analysis complete — no significant gaps."
        return await self.send_webhook(content, embed)

    async def post_meme(self, caption: str, meme_path: str) -> bool:
        """Post a generated meme to Discord."""
        content = f"🎭 **New eigenforensics meme**\n{caption}"
        return await self.send_webhook(content, file_path=meme_path)

    async def post_leaderboard_update(self, leaderboard_data: dict) -> bool:
        """Post leaderboard update to Discord."""
        top = leaderboard_data.get("leaderboard", [])[:5]
        if not top:
            return True

        lines = ["🏆 **FOIA Researcher Leaderboard**\n"]
        for i, researcher in enumerate(top):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
            lines.append(f"{medal} **{researcher['name']}** — {researcher['score']:.1f} pts "
                         f"({researcher['gaps_closed']} gaps closed)")

        stats = leaderboard_data.get("stats", {})
        lines.append(f"\n📊 Total researchers: {stats.get('total_researchers', 0)} | "
                     f"Gaps closed: {stats.get('total_gaps_closed', 0)}")

        return await self.send_webhook("\n".join(lines))

    async def post_weekly_roast(self, report: dict, top_gaps: list) -> bool:
        """Post the weekly gap roast summary."""
        embed = {
            "title": "🔥 Weekly Gap Roast",
            "description": "The most structurally broken documents this week",
            "color": 0xFF6600,
            "fields": [],
            "footer": {"text": "disclosure.tools — eigenforensics with receipts"},
        }

        for i, gap in enumerate(top_gaps[:5]):
            embed["fields"].append({
                "name": f"#{i+1} — {gap.get('location', 'Unknown')}",
                "value": f"Severity: {gap.get('severity', 'unknown')} | "
                         f"Category: {gap.get('category', 'unknown')}\n"
                         f"{gap.get('description', '')}",
                "inline": False,
            })

        content = "🔥 **WEEKLY GAP ROAST** — Time to shame some structural incompleteness!"
        return await self.send_webhook(content, embed)

    async def close(self):
        await self.client.aclose()


# Singleton instance
bot = DisclosureDiscordBot()

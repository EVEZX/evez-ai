"""ClawBreak Channel Support — connect to Telegram, Discord, Slack, etc."""
import os
import json
import httpx
import asyncio
from typing import Optional

class ChannelManager:
    """Manage multiple chat channels for ClawBreak."""

    def __init__(self, config, process_fn):
        """
        config: ClawBreak config
        process_fn: async function(message, session_id) -> reply
        """
        self.config = config
        self.process_fn = process_fn
        self.channels = config.data.get("channels", {})
        self._tasks = []

    async def start_all(self):
        """Start polling/webhook for all configured channels."""
        if self.channels.get("telegram", {}).get("enabled"):
            self._tasks.append(asyncio.create_task(self._telegram_poll()))
        if self.channels.get("discord", {}).get("enabled"):
            self._tasks.append(asyncio.create_task(self._discord_poll()))
        # Slack and others would go here

    async def stop_all(self):
        """Stop all channel listeners."""
        for t in self._tasks:
            t.cancel()

    # --- Telegram ---
    async def _telegram_poll(self):
        """Long-poll Telegram for messages."""
        token = self.channels["telegram"].get("token")
        if not token:
            return

        base = f"https://api.telegram.org/bot{token}"
        offset = 0
        session_map = {}  # chat_id -> session_id

        while True:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(f"{base}/getUpdates", json={
                        "offset": offset,
                        "timeout": 25,
                        "allowed_updates": ["message"],
                    })
                    data = resp.json()

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    text = msg.get("text", "")

                    if not text or text.startswith("/"):
                        if text == "/start":
                            await self._telegram_send(base, chat_id, "⚡ ClawBreak is online. Send me a message.")
                        continue

                    # Get or create session
                    session_id = session_map.get(chat_id, f"tg_{chat_id}")
                    session_map[chat_id] = session_id

                    # Process through AI
                    reply = await self.process_fn(text, session_id)

                    # Send reply (split if too long)
                    await self._telegram_send(base, chat_id, reply[:4096])

            except asyncio.CancelledError:
                return
            except Exception as e:
                print(f"Telegram poll error: {e}")
                await asyncio.sleep(5)

    async def _telegram_send(self, base_url, chat_id, text):
        """Send a Telegram message."""
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })

    # --- Discord ---
    async def _discord_poll(self):
        """Discord bot via gateway (simplified - uses webhook for outbound)."""
        token = self.channels["discord"].get("token")
        if not token:
            return

        # Discord requires websocket gateway - simplified version
        # For full Discord support, use discord.py in a plugin
        print("Discord channel: Use the discord.py plugin for full support")
        return

    # --- Slack (webhook-based) ---
    async def slack_send(self, webhook_url, text):
        """Send a message to Slack via webhook."""
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(webhook_url, json={"text": text})

    # --- Email (via Composio) ---
    async def email_send(self, mcp_client, to, subject, body):
        """Send an email through Composio MCP."""
        return await mcp_client.call_tool("composio", "COMPOSIO_MULTI_EXECUTE_TOOL", {
            "tools": [{"tool_slug": "GMAIL_SEND_EMAIL", "arguments": {"to": to, "subject": subject, "body": body}}],
            "sync_response_to_workbench": False,
        })
PYEOF
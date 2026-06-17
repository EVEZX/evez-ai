"""
EVEZ Telegram Mesh Cortex — bot command handler bridging Telegram to OpenClaw gateway.
"""
import os
import sys
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
)
try:
    from nomad_vault import load_config
except ImportError:
    def load_config(k, d=None): return os.environ.get(k, d)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

GATEWAY = os.environ.get("OPENCLAW_GATEWAY_URL", "http://localhost:18789")
GATEWAY_TOKEN = load_config("OPENCLAW_GATEWAY_TOKEN", "")

def gw(path: str, payload: dict) -> dict:
    try:
        r = requests.post(
            f"{GATEWAY}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"},
            timeout=30
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ CLAW GOBLIN ONLINE\n"
        "Commands:\n"
        "/status — mesh health\n"
        "/sync — gateway sync\n"
        "/brief — morning brief\n"
        "/goblin <cmd> — full goblin mode\n"
        "/audit <repo> — trigger security audit\n"
        "/issue <repo> <title> — create GitHub issue"
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(">> Checking mesh status...")
    result = gw("/health", {})
    await update.message.reply_text(f"✓ Gateway: {result.get('status', 'unknown')}")

async def cmd_sync(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(">> Gateway sync initiated...")
    result = gw("/agent/full_sync", {"trigger": "full system sync"})
    await update.message.reply_text(f"✓ {result.get('message', str(result))}")

async def cmd_brief(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(">> Generating morning brief...")
    result = gw("/agent/morning_brief", {})
    brief = result.get("message", result.get("error", str(result)))
    await update.message.reply_text(f"📋 Morning Brief:\n{brief}")

async def cmd_goblin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args) if ctx.args else ""
    if not text:
        await update.message.reply_text("Usage: /goblin <command>")
        return
    await update.message.reply_text(f"⚡ GOBLIN MODE: {text}")
    result = gw("/chat", {"message": text, "profile": "goblin"})
    response = result.get("response", result.get("error", str(result)))
    await update.message.reply_text(f"🦖 {response[:4000]}")

async def cmd_audit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    repo = ctx.args[0] if ctx.args else "EvezArt/evez-os"
    if "/" not in repo:
        repo = f"EvezArt/{repo}"
    await update.message.reply_text(f">> Triggering audit on {repo}...")
    result = gw("/github", {"action": "audit_all", "repo": repo, "ref": "main"})
    await update.message.reply_text(f"✓ {result.get('details', str(result))}")

async def cmd_issue(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args or []
    repo = args[0] if args else "EvezArt/evez-os"
    title = " ".join(args[1:]) if len(args) > 1 else "CLAW GOBLIN task"
    if "/" not in repo:
        repo = f"EvezArt/{repo}"
    result = gw("/github", {
        "action": "create_issue",
        "repo": repo,
        "title": title,
        "body": f"Created via CLAW GOBLIN Telegram cortex.\nOperator: @{update.effective_user.username}"
    })
    url = result.get("url", "")
    await update.message.reply_text(f"✓ Issue created: {url or str(result)}")

async def passthrough(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Treat any non-command message as a goblin mode prompt."""
    text = update.message.text
    result = gw("/chat", {"message": text, "profile": "goblin"})
    response = result.get("response", result.get("error", str(result)))
    await update.message.reply_text(f"🦖 {response[:4000]}")

if __name__ == "__main__":
    token = load_config("TELEGRAM_BOT_TOKEN")
    if not token:
        print("!! TELEGRAM_BOT_TOKEN missing from vault/env.")
        sys.exit(1)

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("sync",   cmd_sync))
    app.add_handler(CommandHandler("brief",  cmd_brief))
    app.add_handler(CommandHandler("goblin", cmd_goblin))
    app.add_handler(CommandHandler("audit",  cmd_audit))
    app.add_handler(CommandHandler("issue",  cmd_issue))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, passthrough))

    print(">> EVEZ Telegram Cortex active. Listening...")
    app.run_polling()
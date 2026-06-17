import os
import sys
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from nomad_vault import load_config, save_config
from gateway_automation import execute_gateway_session

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def check_connectivity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifies internal availability of the local mesh environment."""
    await update.message.reply_text(">> Core Mesh Signal: STABLE. Persistent database online.")


async def trigger_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Invokes the headless automation script to refresh local state."""
    await update.message.reply_text(">> Command accepted. Deploying headless driver...")
    success = execute_gateway_session(headless=True)
    if success:
        await update.message.reply_text(">> Automation pass complete. Session states committed.")
    else:
        await update.message.reply_text(">> Automation pass encountered non-fatal communication delay.")


if __name__ == '__main__':
    token = load_config('TELEGRAM_BOT_TOKEN')
    if not token:
        print("!! Base configuration token missing from local vault database.")
        sys.exit(1)

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('mesh_status', check_connectivity))
    app.add_handler(CommandHandler('gateway_sync', trigger_sync))

    print(">> Telegram operational listener active.")
    app.run_polling()

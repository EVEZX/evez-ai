import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from nomad_vault import load_config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def status_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(">> Evez System: ONLINE. Cognition Mesh: STABLE.")


async def restart_mesh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(">> Command Received. Initiating Mesh Compaction...")
    # os.system('python3 compaction_protocol.py')


if __name__ == '__main__':
    token = load_config('TELEGRAM_BOT_TOKEN')
    if not token:
        print("!! No Token Found. Run nomad_vault.py to set keys first.")
        exit()

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler('status', status_check))
    application.add_handler(CommandHandler('compact', restart_mesh))

    print(">> Cortex Listener Active. Waiting for signals...")
    application.run_polling()

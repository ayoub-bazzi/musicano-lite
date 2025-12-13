from telegram import Update
from telegram.ext import ContextTypes
# We import your existing nice menu from menus.py
from handlers.menus import start as menu_start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Redirects to the main menu."""
    await menu_start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Basic help command."""
    await update.message.reply_text(
        "👋 **Musicano Lite Help**\n\n"
        "Use /start to open the main menu.\n"
        "Send me a song name to search and download it (Coming Soon).",
        parse_mode="Markdown"
    )
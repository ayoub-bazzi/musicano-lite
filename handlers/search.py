from telegram import Update
from telegram.ext import ContextTypes

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (Search or Playlist Links)."""
    text = update.message.text
    
    # 1. Check if it's a Spotify Link (for your Sync feature)
    if "spotify.com" in text:
        from handlers.menus import handle_playlist_input
        await handle_playlist_input(update, context)
        return

    # 2. Otherwise, treat it as a Song Search
    await update.message.reply_text(f"🔎 Searching for: **{text}**...\n\n(Music download logic goes here)", parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle generic callbacks."""
    query = update.callback_query
    await query.answer()
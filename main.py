import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
    ContextTypes
)
from keep_alive import keep_alive
from database import init_db
from config import BOT_TOKEN

# --- Import Handlers ---
from handlers import menus
from handlers.search import handle_message
from services.sync_manager import sync_channel_logic

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- The Router ---
async def global_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "start_menu" or data == "my_channels":
        await menus.my_channels(update, context)
        return
    if data == "connect_flow":
        await menus.connect_start(update, context)
        return
    if data.startswith("dash_"):
        await menus.channel_dashboard(update, context)
        return
    if data.startswith("unlink_"):
        await menus.unlink_channel(update, context)
        return
    if data.startswith("sync_run_"):
        await sync_channel_logic(update, context)
        return
    await query.answer()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menus.start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to see menu. Send a song name to download it.")

# --- HELPER: Setup Cookies ---
def setup_cookies():
    """Writes the cookies from ENV variable to a file for yt-dlp to use."""
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if cookies_content:
        with open("cookies.txt", "w") as f:
            f.write(cookies_content)
        print("✅ Cookies file created successfully.")
    else:
        print("⚠️ WARNING: No YOUTUBE_COOKIES found in Environment Variables!")

def main():
    # 1. Start Web Server
    keep_alive()

    # 2. Setup Cookies (CRITICAL FIX)
    setup_cookies()

    # 3. Initialize Database
    init_db()

    # 4. Build Bot
    print("🚀 Starting Musicano Lite...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(ChatMemberHandler(menus.on_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(global_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
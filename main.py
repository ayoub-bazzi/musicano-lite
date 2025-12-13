import logging
import os
from telegram import Update, BotCommand
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

from handlers import menus
from handlers.search import handle_message
from services.sync_manager import sync_channel_logic

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
    text = (
        "📚 **Musicano Lite Logic**\n\n"
        "1. **Channels:** Add me as Admin to a channel -> Send me a Spotify Playlist Link.\n"
        "2. **Sync:** Go to 'My Channels' -> 'Sync Now' to mirror the playlist to the channel.\n"
        "3. **Search:** Just text me a song name to download it."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 **Contact Support:**\n\nDeveloper: @Uzomaki_Dev", parse_mode="Markdown")

# --- Helper: Set Menu Commands ---
async def post_init(application):
    """Sets the menu button commands on startup."""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "See how the bot works"),
        BotCommand("contact", "Contact the Developer"),
    ]
    await application.bot.set_my_commands(commands)
    print("✅ Menu Commands Set Successfully")

# --- Helper: Setup Cookies ---
def setup_cookies():
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if cookies_content:
        with open("cookies.txt", "w") as f:
            f.write(cookies_content)
        print("✅ Cookies file created.")
    else:
        print("⚠️ WARNING: No YOUTUBE_COOKIES found!")

def main():
    keep_alive()
    setup_cookies()
    init_db()

    print("🚀 Starting Musicano Lite...")
    
    # We add post_init here to run the command setter
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("contact", contact_command)) # Added Contact
    
    app.add_handler(ChatMemberHandler(menus.on_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(global_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
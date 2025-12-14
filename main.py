import logging
import os
from telegram import Update, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
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
from database import init_db, register_user, get_bot_stats
from config import BOT_TOKEN, BOT_VERSION

from handlers import menus
from handlers.search import handle_message
from services.sync_manager import sync_channel_logic

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def global_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes callback queries to appropriate handlers."""
    query = update.callback_query
    data = query.data
    
    # Menu Navigation
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
    """Handles /start command and registers user."""
    user = update.effective_user
    register_user(user.id)
    await menus.start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays help text."""
    await update.message.reply_text("Use /start to see menu. Send a song name to download it.")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays bot statistics and version information."""
    try:
        user_count, dl_count = get_bot_stats()
        
        text = (
            f"ℹ️ **About Musicano Lite**\n\n"
            f"🔺 **Version:** `{BOT_VERSION}`\n"
            f"🔻 **Name:** @MusicanoLiteBot\n"
            f"✒️ **Contact us:** @Uzomaki_Dev\n"
            f"💵 **Donation:** /donate\n"
            f"📣 **Our channel:** [UzomakiDev](https://t.me/UzomakiDev)\n"
            f"👥 **Users:** `{user_count}`\n"
            f"⬇️ **Total downloads:** `{dl_count}`"
        )
        
        keyboard = [[InlineKeyboardButton("📣 Join Channel", url="https://t.me/UzomakiDev")]]
        
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logging.error(f"About command error: {e}")
        await update.message.reply_text("❌ Stats currently unavailable.")

async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays donation information."""
    text = (
        "❤️ **Support Musicano Lite**\n\n"
        "Servers and maintenance cost money. If you like this bot, consider buying us a coffee!\n"
    )
    donate_url = "https://t.me/Uzomaki_Dev" 
    keyboard = [[InlineKeyboardButton("☕ Donate", url=donate_url)]]
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def post_init(application):
    """Registers bot commands with Telegram API on startup."""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "How to use"),
        BotCommand("about", "Bot Info & Stats"),
        BotCommand("donate", "Support us"),
    ]
    await application.bot.set_my_commands(commands)
    print("✅ Menu Commands Set Successfully")

def setup_cookies():
    """Initializes cookies.txt from environment variable for yt-dlp."""
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if cookies_content:
        with open("cookies.txt", "w") as f:
            f.write(cookies_content)

def main():
    """Entry point."""
    keep_alive()
    setup_cookies()
    init_db()

    print("🚀 Starting Musicano Lite...")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("donate", donate_command))
    
    # Admin & Logic Handlers
    app.add_handler(ChatMemberHandler(menus.on_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(global_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
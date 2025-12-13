import logging
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
    
    # 1. Menus
    if data == "start_menu" or data == "my_channels":
        await menus.my_channels(update, context)
        return

    if data == "connect_flow":
        await menus.connect_start(update, context)
        return

    # 2. Channel Dashboard
    if data.startswith("dash_"):
        await menus.channel_dashboard(update, context)
        return

    # 3. Unlink
    if data.startswith("unlink_"):
        await menus.unlink_channel(update, context)
        return

    # 4. Sync Run
    if data.startswith("sync_run_"):
        await sync_channel_logic(update, context)
        return

    await query.answer()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menus.start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to see menu. Send a song name to download it.")

def main():
    # 1. Start Web Server
    keep_alive()

    # 2. Initialize Database (PostgreSQL)
    init_db()

    # 3. Build Bot
    print("🚀 Starting Musicano Lite...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 4. Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Detect when bot is added to a channel
    app.add_handler(ChatMemberHandler(menus.on_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))

    # Button Clicks
    app.add_handler(CallbackQueryHandler(global_callback_handler))
    
    # Text Messages (Search or Links)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 5. Run
    app.run_polling()

if __name__ == "__main__":
    main()
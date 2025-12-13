import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from keep_alive import keep_alive
from database import init_db
from config import BOT_TOKEN

# --- Import your specific Menu Handlers ---
from handlers import menus
from handlers.search import handle_message

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- The Router: This decides which function handles the button click ---
async def global_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    # 1. Main Menu & My Channels
    if data == "start_menu" or data == "my_channels":
        await menus.my_channels(update, context)
        return

    # 2. Connect Flow
    if data == "connect_flow":
        await menus.connect_start(update, context)
        return

    # 3. Channel Dashboard (e.g., dash_123)
    if data.startswith("dash_"):
        await menus.channel_dashboard(update, context)
        return

    # 4. Unlink Channel (e.g., unlink_123)
    if data.startswith("unlink_"):
        await menus.unlink_channel(update, context)
        return

    # 5. Sync Run (e.g., sync_run_123)
    # (Make sure you have a sync function in menus.py, otherwise this button won't do anything yet)
    if data.startswith("sync_run_"):
        await query.answer("Sync feature coming soon!")
        return

    # If unknown
    await query.answer()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Override standard start to show the nice menu"""
    await menus.start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to see the menu options.")

def main():
    # 1. Start the fake website
    keep_alive()

    # 2. Initialize Database
    init_db()

    # 3. Build the Bot
    print("🚀 Starting Musicano Lite (With Menu Routing)...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 4. Add Handlers
    app.add_handler(CommandHandler("start", start_command)) # Use the fancy menu start
    app.add_handler(CommandHandler("help", help_command))
    
    # This is the important part: Connect the buttons to the router!
    app.add_handler(CallbackQueryHandler(global_callback_handler))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 5. Run
    app.run_polling()

if __name__ == "__main__":
    main()
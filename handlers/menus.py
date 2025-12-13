# handlers/menus.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes, ConversationHandler
from database import get_user_channels, get_channel, add_channel, delete_channel

# States for ConversationHandler
WAITING_FOR_PLAYLIST = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point."""
    text = "👋 **Welcome to Musicano Lite**\n\nI mirror Spotify Playlists to Telegram Channels."
    keyboard = [
        [InlineKeyboardButton("🔗 Connect Channel", callback_data="connect_flow")],
        [InlineKeyboardButton("📂 My Channels", callback_data="my_channels")]
    ]
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def my_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    channels = get_user_channels(user_id)
    keyboard = []
    
    if not channels:
        text = "You have no connected channels."
        keyboard.append([InlineKeyboardButton("🔗 Connect Now", callback_data="connect_flow")])
    else:
        text = "📂 **Select a Channel:**"
        for ch in channels:
            # ch[0]=id, ch[2]=title
            keyboard.append([InlineKeyboardButton(f"📢 {ch[2]}", callback_data=f"dash_{ch[0]}")])
            
    keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="start_menu")])
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def channel_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channel_id = int(query.data.split("_")[1])
    
    channel = get_channel(channel_id)
    if not channel:
        await query.edit_message_text("❌ Channel not found.")
        return

    text = (
        f"📢 **{channel[2]}**\n"
        f"🔗 [Spotify Playlist]({channel[3]})\n\n"
        "Select an action:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Sync Now", callback_data=f"sync_run_{channel_id}")],
        [InlineKeyboardButton("❌ Unlink", callback_data=f"unlink_{channel_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="my_channels")]
    ]
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def unlink_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    channel_id = int(query.data.split("_")[1])
    delete_channel(channel_id)
    await query.answer("Channel Unlinked!")
    await my_channels(update, context)

# --- Connection Flow ---
async def connect_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🔗 **How to Connect:**\n\n"
        "1. Add me to your Channel as an **Admin**.\n"
        "2. Once added, I will detect it automatically.\n"
        "3. I will then ask you for the Playlist Link."
    )
    await query.edit_message_text(text, parse_mode="Markdown")
    # Note: The actual logic relies on ChatMemberHandler in main.py

async def on_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detects when bot is added to a channel."""
    update_data = update.my_chat_member
    if update_data.new_chat_member.status == ChatMember.ADMINISTRATOR:
        chat_id = update_data.chat.id
        title = update_data.chat.title
        user = update_data.from_user
        
        # Save temp data
        context.user_data['pending_channel_id'] = chat_id
        context.user_data['pending_channel_title'] = title
        context.user_data['state'] = WAITING_FOR_PLAYLIST
        
        await context.bot.send_message(user.id, f"✅ I've been added to **{title}**!\n\nNow send me the **Spotify Playlist Link**.")

async def handle_playlist_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == WAITING_FOR_PLAYLIST:
        link = update.message.text.strip()
        if "spotify.com" in link:
            c_id = context.user_data['pending_channel_id']
            c_title = context.user_data['pending_channel_title']
            user_id = update.effective_user.id
            
            add_channel(c_id, user_id, c_title, link)
            
            context.user_data.clear()
            await update.message.reply_text("✅ **Connected!**\nUse /start > My Channels to sync.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Invalid link. Please send a valid Spotify URL.")
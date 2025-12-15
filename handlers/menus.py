# handlers/menus.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes, ConversationHandler
from database import get_user_channels, get_channel, add_channel, delete_channel
from config import REQUIRED_CHANNEL

# States for ConversationHandler
WAITING_FOR_PLAYLIST = 1

logger = logging.getLogger(__name__)

async def check_channel_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if user is a member of the required channel."""
    try:
        # Get chat member status for the required channel
        chat_member = await context.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL,
            user_id=user_id
        )
        # User is a member if status is not "left" or "kicked"
        return chat_member.status not in ["left", "kicked"]
    except Exception as e:
        logger.error(f"Error checking channel membership for user {user_id}: {e}")
        # If we can't check, allow access (fail-open for now)
        return True

async def show_join_requirement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show join requirement message with buttons."""
    text = (
        "📢 **Join Required**\n\n"
        "To use Musicano Lite, you need to join our official channel:\n"
        f"{REQUIRED_CHANNEL}\n\n"
        "After joining, click '✅ I Joined' to verify."
    )
    
    keyboard = [
        [InlineKeyboardButton("📣 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'I Joined' button click - recheck membership."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check membership
    is_member = await check_channel_membership(context, user_id)
    
    if is_member:
        # User has joined, show main menu
        text = "✅ **Welcome!**\n\nYou've successfully joined the channel. Enjoy Musicano Lite!"
        keyboard = [
            [InlineKeyboardButton("🔗 Connect Channel", callback_data="connect_flow")],
            [InlineKeyboardButton("📂 My Channels", callback_data="my_channels")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # User still hasn't joined
        text = (
            "❌ **Not Joined Yet**\n\n"
            "I still can't see you in the channel. Please make sure:\n"
            "1. You've actually joined the channel\n"
            "2. You're not just a pending request\n"
            "3. Try clicking the join button below\n\n"
            "After joining, click '✅ I Joined' again."
        )
        keyboard = [
            [InlineKeyboardButton("📣 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
            [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point with channel membership check."""
    user_id = update.effective_user.id
    
    # Check if user is a member of the required channel
    is_member = await check_channel_membership(context, user_id)
    
    if not is_member:
        await show_join_requirement(update, context)
        return
    
    # User is a member, show main menu
    text = "👋 **Welcome to Musicano Lite**\n\nI mirror Spotify Playlists to Telegram Channels."
    keyboard = [
        [InlineKeyboardButton("🔗 Connect Channel", callback_data="connect_flow")],
        [InlineKeyboardButton("📂 My Channels", callback_data="my_channels")],
        [InlineKeyboardButton("🔍 Search Song", callback_data="search_song")]
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

async def handle_search_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show search instructions when search button is clicked."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🔍 **Search Song**\n\n"
        "You can search for songs in two ways:\n\n"
        "1. **Song Name** - Write the song name and artist\n"
        "   Example: `Shape of You Ed Sheeran`\n\n"
        "2. **Spotify Link** - Paste a Spotify track link\n"
        "   Example: `https://open.spotify.com/track/...`\n\n"
        "Just send me the song name or link directly!"
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="start_menu")]]
    
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

import os
import shutil
import uuid
from telegram import Update
from telegram.ext import ContextTypes
from services.youtube_client import youtube_client

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (Search or Playlist Links)."""
    text = update.message.text
    
    # 1. Check if it's a Spotify Link (Sync Feature)
    if "spotify.com" in text or "open.spotify.com" in text:
        from handlers.menus import handle_playlist_input
        await handle_playlist_input(update, context)
        return

    # 2. General Search Logic
    status_msg = await update.message.reply_text(f"🔎 **Searching:** {text}...", parse_mode="Markdown")
    
    temp_dir = f"temp_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    file_path_base = os.path.join(temp_dir, "download")

    try:
        # Download
        downloaded_path = await youtube_client.download_song(text, file_path_base)
        
        if downloaded_path and os.path.exists(downloaded_path):
            await status_msg.edit_text(f"⬆️ **Uploading...**")
            
            with open(downloaded_path, 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio, 
                    title=text, 
                    performer="Musicano Bot"
                )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Could not find or download that song.")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
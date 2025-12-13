import os
import shutil
import uuid
from telegram import Update
from telegram.ext import ContextTypes
from services.youtube_client import youtube_client

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (Search or Playlist Links)."""
    text = update.message.text
    
    if "spotify.com" in text or "open.spotify.com" in text:
        from handlers.menus import handle_playlist_input
        await handle_playlist_input(update, context)
        return

    status_msg = await update.message.reply_text(f"🔎 **Searching:** {text}...", parse_mode="Markdown")
    
    temp_dir = f"temp_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    file_path_base = os.path.join(temp_dir, "download")

    try:
        # Now returns a tuple (audio, thumbnail)
        audio_path, thumb_path = await youtube_client.download_song(text, file_path_base)
        
        if audio_path and os.path.exists(audio_path):
            await status_msg.edit_text(f"⬆️ **Uploading...**")
            
            with open(audio_path, 'rb') as audio_file:
                if thumb_path and os.path.exists(thumb_path):
                    with open(thumb_path, 'rb') as thumb_file:
                        await update.message.reply_audio(
                            audio=audio_file, 
                            thumbnail=thumb_file,  # <--- SEND COVER
                            title=text, 
                            performer="Musicano Bot"
                        )
                else:
                    await update.message.reply_audio(
                        audio=audio_file, 
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
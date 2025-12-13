import os
import shutil
import uuid
from telegram import Update
from telegram.ext import ContextTypes
from services.youtube_client import youtube_client
from services.spotify_client import spotify_client # Import this!

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (Search or Playlist Links)."""
    text = update.message.text
    
    # --- 1. HANDLE SPOTIFY PLAYLISTS (Sync Feature) ---
    if "spotify.com" in text and "/playlist/" in text:
        from handlers.menus import handle_playlist_input
        await handle_playlist_input(update, context)
        return

    # --- 2. HANDLE SPOTIFY TRACKS (Fix for DRM Error) ---
    if "spotify.com" in text and "/track/" in text:
        status_msg = await update.message.reply_text("🔎 **Converting Spotify Link...**", parse_mode="Markdown")
        
        # Get the "Artist - Song Name" from Spotify
        search_query = spotify_client.get_track_info(text)
        
        if not search_query:
            await status_msg.edit_text("❌ Invalid Spotify Link or API Error.")
            return
            
        # Update variable 'text' so the next step downloads the query, not the URL
        text = search_query
        await status_msg.edit_text(f"🔎 **Searching:** {text}...")
    else:
        # Standard Search
        status_msg = await update.message.reply_text(f"🔎 **Searching:** {text}...", parse_mode="Markdown")
    
    # --- 3. DOWNLOAD LOGIC (YouTube Search) ---
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
                            thumbnail=thumb_file,
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
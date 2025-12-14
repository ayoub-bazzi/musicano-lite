import os
import shutil
import uuid
import urllib.request
from telegram import Update
from telegram.ext import ContextTypes
from services.youtube_client import youtube_client
from services.spotify_client import spotify_client
from database import increment_downloads

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "spotify.com" in text and "/playlist/" in text:
        from handlers.menus import handle_playlist_input
        await handle_playlist_input(update, context)
        return

    search_query = None
    cover_url = None
    song_title = None
    artist_name = None

    if "spotify.com" in text and "/track/" in text:
        info = spotify_client.get_track_info(text)
        if info:
            search_query, cover_url, song_title, artist_name = info
    else:
        info = spotify_client.search_track(text)
        if info:
            search_query, cover_url, song_title, artist_name = info
        else:
            search_query = text

    display_name = f"{artist_name} - {song_title}" if song_title else text
    status_msg = await update.message.reply_text(f"⬇️ **Downloading:** {display_name}...", parse_mode="Markdown")

    # --- 3. DOWNLOAD ---
    temp_dir = f"temp_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    file_path_base = os.path.join(temp_dir, "download")
    
    cover_path = None

    try:
        # Download Cover
        if cover_url:
            cover_path = os.path.join(temp_dir, "cover.jpg")
            try:
                urllib.request.urlretrieve(cover_url, cover_path)
            except:
                cover_path = None

        # Download Audio
        audio_path, _ = await youtube_client.download_song(search_query, file_path_base)
        
        if audio_path and os.path.exists(audio_path):
            await status_msg.edit_text(f"⬆️ **Uploading...**")
            
            # --- INCREMENT STATS HERE ---
            increment_downloads() 
            # ----------------------------

            with open(audio_path, 'rb') as audio_file:
                if cover_path and os.path.exists(cover_path):
                    with open(cover_path, 'rb') as thumb_file:
                        await update.message.reply_audio(
                            audio=audio_file, 
                            thumbnail=thumb_file,
                            title=song_title if song_title else text, 
                            performer=artist_name if artist_name else "Musicano Bot"
                        )
                else:
                    await update.message.reply_audio(
                        audio=audio_file, 
                        title=song_title if song_title else text, 
                        performer=artist_name if artist_name else "Musicano Bot"
                    )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Could not download song.")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
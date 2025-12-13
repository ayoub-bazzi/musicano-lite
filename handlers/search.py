import os
import shutil
import uuid
import urllib.request
from telegram import Update
from telegram.ext import ContextTypes
from services.youtube_client import youtube_client
from services.spotify_client import spotify_client

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (Search or Playlist Links)."""
    text = update.message.text
    user_query = text # Keep original text for fallback
    
    # Variables to hold metadata
    search_query = None
    cover_url = None
    song_title = None
    artist_name = None

    # --- 1. HANDLE SPOTIFY PLAYLISTS ---
    if "spotify.com" in text and "/playlist/" in text:
        from handlers.menus import handle_playlist_input
        await handle_playlist_input(update, context)
        return

    status_msg = await update.message.reply_text("🔎 **Searching...**", parse_mode="Markdown")

    # --- 2. IDENTIFY INPUT TYPE ---
    if "spotify.com" in text and "/track/" in text:
        # It's a Spotify Link
        info = spotify_client.get_track_info(text)
        if info:
            search_query, cover_url, song_title, artist_name = info
    else:
        # It's a Text Search -> Search Spotify First for High Quality Cover
        info = spotify_client.search_track(text)
        if info:
            search_query, cover_url, song_title, artist_name = info
        else:
            # Fallback: Just search YouTube with raw text if Spotify fails
            search_query = text

    # Update status
    display_name = f"{artist_name} - {song_title}" if song_title else text
    await status_msg.edit_text(f"⬇️ **Downloading:** {display_name}...")

    # --- 3. DOWNLOAD PROCESS ---
    temp_dir = f"temp_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    file_path_base = os.path.join(temp_dir, "download")
    
    cover_path = None

    try:
        # A. Download High-Res Cover (if we found one on Spotify)
        if cover_url:
            cover_path = os.path.join(temp_dir, "cover.jpg")
            try:
                urllib.request.urlretrieve(cover_url, cover_path)
            except Exception as e:
                print(f"Cover Download Error: {e}")
                cover_path = None

        # B. Download Audio from YouTube
        audio_path, _ = await youtube_client.download_song(search_query, file_path_base)
        
        if audio_path and os.path.exists(audio_path):
            await status_msg.edit_text(f"⬆️ **Uploading...**")
            
            with open(audio_path, 'rb') as audio_file:
                # Use Spotify Cover if available, otherwise None
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
            await status_msg.edit_text("❌ Could not download song. (DRM or YouTube Error)")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
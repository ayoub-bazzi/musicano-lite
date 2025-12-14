import os
import shutil
import uuid
import urllib.request
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from services.youtube_client import youtube_client
from services.spotify_client import spotify_client
from database import increment_downloads
from queue_manager import download_queue

async def _download_and_send(update: Update, search_query: str, cover_url: str, 
                           song_title: str, artist_name: str, text: str):
    """Actual download logic - called by queue manager"""
    display_name = f"{artist_name} - {song_title}" if song_title else text
    
    temp_dir = f"temp_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    file_path_base = os.path.join(temp_dir, "download")
    
    final_cover_path = None

    try:
        # A. Try to download Spotify Cover (High Quality)
        if cover_url:
            spotify_cover_path = os.path.join(temp_dir, "spotify_cover.jpg")
            try:
                urllib.request.urlretrieve(cover_url, spotify_cover_path)
                final_cover_path = spotify_cover_path
            except:
                pass

        # B. Download Audio + YouTube Backup Cover (with timeout)
        try:
            audio_path, yt_thumb_path = await asyncio.wait_for(
                youtube_client.download_song(search_query, file_path_base),
                timeout=120  # 2 minute timeout for free tier
            )
        except asyncio.TimeoutError:
            await update.message.reply_text("❌ Download timeout. Please try again.")
            return None
        
        # C. Decide which cover to use
        if not final_cover_path and yt_thumb_path and os.path.exists(yt_thumb_path):
            final_cover_path = yt_thumb_path

        if audio_path and os.path.exists(audio_path):
            increment_downloads()

            with open(audio_path, 'rb') as audio_file:
                if final_cover_path and os.path.exists(final_cover_path):
                    with open(final_cover_path, 'rb') as thumb_file:
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
            return True
        else:
            await update.message.reply_text("❌ Could not download song.")
            return False
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
        return False
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    # 1. Handle Playlist Links (Sync) - bypass queue for now
    if "spotify.com" in text and "/playlist/" in text:
        from handlers.menus import handle_playlist_input
        await handle_playlist_input(update, context)
        return

    # 2. Metadata Setup
    search_query = text
    cover_url = None
    song_title = None
    artist_name = None

    # Check Spotify for Metadata
    if "spotify.com" in text and "/track/" in text:
        info = spotify_client.get_track_info(text)
        if info: search_query, cover_url, song_title, artist_name = info
    else:
        info = spotify_client.search_track(text)
        if info: 
            search_query, cover_url, song_title, artist_name = info
        else:
            # Fallback: Spotify didn't find it, so search_query remains just the text
            search_query = text

    display_name = f"{artist_name} - {song_title}" if song_title else text
    
    # Send initial status message
    status_msg = await update.message.reply_text(
        f"🎵 **Request:** {display_name}\n"
        f"⏳ **Checking queue...**",
        parse_mode="Markdown"
    )
    
    # Add to queue
    queue_result = await download_queue.add_to_queue(
        user_id,
        _download_and_send,
        update, search_query, cover_url, song_title, artist_name, text
    )
    
    # Update user based on queue result
    if queue_result["status"] == "started":
        await status_msg.edit_text(
            f"🎵 **Request:** {display_name}\n"
            f"✅ **Status:** Download started immediately!\n"
            f"📊 **Active downloads:** {download_queue.get_queue_stats()['active_downloads']}/2",
            parse_mode="Markdown"
        )
    elif queue_result["status"] == "queued":
        await status_msg.edit_text(
            f"🎵 **Request:** {display_name}\n"
            f"⏳ **Status:** Added to queue at position {queue_result['position']}\n"
            f"📊 **Queue:** {queue_result['position']} waiting, {download_queue.get_queue_stats()['active_downloads']}/2 active",
            parse_mode="Markdown"
        )
    elif queue_result["status"] == "already_active":
        await status_msg.edit_text(
            f"🎵 **Request:** {display_name}\n"
            f"⚠️ **Status:** You already have a download in progress.\n"
            f"Please wait for it to complete before requesting another song.",
            parse_mode="Markdown"
        )
    elif queue_result["status"] == "already_queued":
        await status_msg.edit_text(
            f"🎵 **Request:** {display_name}\n"
            f"⚠️ **Status:** You're already in queue at position {queue_result['position']}.\n"
            f"Please wait for your turn.",
            parse_mode="Markdown"
        )
    elif queue_result["status"] == "queue_full":
        await status_msg.edit_text(
            f"🎵 **Request:** {display_name}\n"
            f"🚫 **Status:** Queue is full (max 5 waiting).\n"
            f"Please try again in a few minutes.",
            parse_mode="Markdown"
        )
    
    # Delete status message after 10 seconds if not started immediately
    if queue_result["status"] in ["queued", "already_queued", "queue_full", "already_active"]:
        await asyncio.sleep(10)
        try:
            await status_msg.delete()
        except:
            pass

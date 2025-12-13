import asyncio
import os
import shutil
import uuid
import logging
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_channel, get_channel_tracks, add_track, delete_track
from services.spotify_client import spotify_client
from services.youtube_client import youtube_client

logger = logging.getLogger(__name__)

async def sync_channel_logic(update, context):
    query = update.callback_query
    channel_id = int(query.data.split("_")[2])
    
    status_msg = await query.edit_message_text(
        text="🛡️ **Safe Mode Sync**\nProcessing songs...",
        parse_mode="Markdown"
    )

    try:
        # 1. Fetch Data
        channel = get_channel(channel_id)
        if not channel:
            await status_msg.edit_text("❌ Channel data not found.")
            return
            
        playlist_link = channel[3]
        
        # 2. Get Lists
        remote_tracks = spotify_client.get_playlist_tracks(playlist_link) 
        local_tracks_map = get_channel_tracks(channel_id)
        
        remote_ids = {t['id'] for t in remote_tracks}
        local_ids = set(local_tracks_map.keys())
        
        to_add_ids = remote_ids - local_ids
        to_remove_ids = local_ids - remote_ids
        
        to_add_items = [t for t in remote_tracks if t['id'] in to_add_ids]
        
        added_count = 0
        removed_count = 0

        # Quick Exit
        if not to_add_items and not to_remove_ids:
            await status_msg.edit_text(
                f"✅ **Up to Date**\nChannel matches Spotify perfectly.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="my_channels")]])
            )
            return

        # 3. Execute REMOVES
        if to_remove_ids:
            await status_msg.edit_text(f"🗑️ Removing {len(to_remove_ids)} songs...")
            for s_id in to_remove_ids:
                try:
                    msg_id = local_tracks_map[s_id]
                    await context.bot.delete_message(chat_id=channel_id, message_id=msg_id)
                    delete_track(s_id)
                    removed_count += 1
                except Exception as e:
                    delete_track(s_id)

        # 4. Execute ADDS
        if to_add_items:
            total_items = len(to_add_items)
            
            for index, track in enumerate(to_add_items):
                if index % 1 == 0:
                    await status_msg.edit_text(
                        f"⏳ **Syncing...**\nProcessing {index+1}/{total_items}: {track['name']}"
                    )

                temp_dir = f"temp_{uuid.uuid4()}"
                os.makedirs(temp_dir, exist_ok=True)
                file_path_base = os.path.join(temp_dir, "song")
                
                try:
                    search_query = f"{track['artist']} - {track['name']} audio"
                    
                    # DOWNLOAD (Now returns tuple)
                    audio_path, thumb_path = await youtube_client.download_song(search_query, file_path_base)
                    
                    if audio_path and os.path.exists(audio_path):
                        # UPLOAD
                        with open(audio_path, 'rb') as audio_file:
                            # Check if we have a thumbnail to send
                            if thumb_path and os.path.exists(thumb_path):
                                with open(thumb_path, 'rb') as thumb_file:
                                    msg = await context.bot.send_audio(
                                        chat_id=channel_id,
                                        audio=audio_file,
                                        thumbnail=thumb_file, # <--- SEND COVER
                                        title=track['name'],
                                        performer=track['artist']
                                    )
                            else:
                                # Fallback without cover
                                msg = await context.bot.send_audio(
                                    chat_id=channel_id,
                                    audio=audio_file,
                                    title=track['name'],
                                    performer=track['artist']
                                )

                        add_track(track['id'], channel_id, msg.message_id, track['name'])
                        added_count += 1
                    else:
                        logger.error(f"Download failed for {track['name']}")

                except Exception as e:
                    logger.error(f"Failed to process {track['name']}: {e}")
                finally:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    await asyncio.sleep(1.0)

        # Final Report
        timestamp = datetime.now().strftime("%H:%M")
        back_btn = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="my_channels")]]
        
        summary = (
            f"📺 *{channel[2]}*\n"
            f"🔄 *Sync Complete*\n"
            f"📥 Added: `{added_count}`\n"
            f"🗑️ Removed: `{removed_count}`"
        )
        
        await status_msg.edit_text(summary, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_btn))

    except Exception as e:
        logger.error(f"Sync Fatal Error: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Error: {e}")
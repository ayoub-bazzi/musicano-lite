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
    
    # Update Status
    status_msg = await query.edit_message_text(
        text="🛡️ **Safe Mode Sync**\nProcessing songs one by one to prevent errors...",
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

        # Quick Exit if nothing to do
        if not to_add_items and not to_remove_ids:
            await status_msg.edit_text(
                f"✅ **Up to Date**\nChannel matches Spotify perfectly.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="my_channels")]])
            )
            return

        # 3. Execute REMOVES first
        if to_remove_ids:
            await status_msg.edit_text(f"🗑️ Removing {len(to_remove_ids)} songs...")
            for s_id in to_remove_ids:
                try:
                    msg_id = local_tracks_map[s_id]
                    await context.bot.delete_message(chat_id=channel_id, message_id=msg_id)
                    delete_track(s_id)
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete message: {e}")
                    # Even if Telegram delete fails, remove from DB so we don't loop forever
                    delete_track(s_id)

        # 4. Execute ADDS (SEQUENTIAL & SAFE)
        if to_add_items:
            total_items = len(to_add_items)
            
            for index, track in enumerate(to_add_items):
                # Update status
                if index % 1 == 0:
                    await status_msg.edit_text(
                        f"⏳ **Syncing...**\nProcessing {index+1}/{total_items}: {track['name']}"
                    )

                temp_dir = f"temp_{uuid.uuid4()}"
                os.makedirs(temp_dir, exist_ok=True)
                file_path = os.path.join(temp_dir, "song.m4a")
                
                try:
                    # Spotify URL
                    spotify_url = f"https://open.spotify.com/track/{track['id']}"
                    
                    # 1. DOWNLOAD
                    downloaded = await youtube_client.download_track(spotify_url, file_path)
                    
                    if downloaded and os.path.exists(downloaded):
                        # FORCE WAIT: Let Windows release the file lock
                        await asyncio.sleep(2.0)
                        
                        # 2. UPLOAD WITH RETRY
                        uploaded = False
                        for attempt in range(3): # Try 3 times
                            try:
                                with open(downloaded, 'rb') as f:
                                    msg = await context.bot.send_audio(
                                        chat_id=channel_id,
                                        audio=f,
                                        title=track['name'],
                                        performer=track['artist']
                                    )
                                # Success!
                                add_track(track['id'], channel_id, msg.message_id, track['name'])
                                added_count += 1
                                uploaded = True
                                break 
                            except PermissionError:
                                logger.warning(f"File locked for {track['name']}, waiting... (Attempt {attempt+1})")
                                await asyncio.sleep(2.0) # Wait 2s and retry
                            except Exception as e:
                                logger.error(f"Upload error: {e}")
                                break
                        
                        if not uploaded:
                            logger.error(f"Failed to upload {track['name']} after 3 attempts.")

                except Exception as e:
                    logger.error(f"Failed to process {track['name']}: {e}")
                finally:
                    # 3. CLEANUP (Delete immediately before moving to next song)
                    try:
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir, ignore_errors=True)
                    except:
                        pass
                    
                    # Tiny pause before next song
                    await asyncio.sleep(1.0)

        # Final Report
        timestamp = datetime.now().strftime("%H:%M")
        back_btn = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="my_channels")]]
        
        summary = (
            f"📺 *{channel[2]}*\n"
            f"🔄 *Status*: ✅ Sync Complete!\n"
            f"⏱️ *Time*: {timestamp}\n\n"
            f"📥 Added: `{added_count}`\n"
            f"🗑️ Removed: `{removed_count}`\n"
            f"📂 Total in Playlist: `{len(remote_tracks)}`"
        )
        
        await status_msg.edit_text(summary, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_btn))

    except Exception as e:
        logger.error(f"Sync Fatal Error: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Error: {e}")
"""
Queue status updater for real-time queue position updates.
This module handles periodic updates to queue status messages.
"""
import asyncio
import logging
from typing import Dict, Optional
from telegram import Message

logger = logging.getLogger(__name__)

class QueueStatusUpdater:
    """Manages real-time updates for queue status messages"""
    
    def __init__(self):
        self.user_status_messages: Dict[int, Message] = {}  # user_id -> status message
        self.user_queue_info: Dict[int, dict] = {}  # user_id -> queue info
        self.update_tasks: Dict[int, asyncio.Task] = {}  # user_id -> update task
        self.lock = asyncio.Lock()
    
    async def register_status_message(self, user_id: int, message: Message, queue_info: dict):
        """Register a status message for a user and start updates"""
        async with self.lock:
            self.user_status_messages[user_id] = message
            self.user_queue_info[user_id] = queue_info
            
            # Start update task if not already running
            if user_id not in self.update_tasks:
                task = asyncio.create_task(self._update_user_status(user_id))
                self.update_tasks[user_id] = task
    
    async def update_queue_position(self, user_id: int, new_position: int, queue_info: dict):
        """Update queue position for a user"""
        async with self.lock:
            if user_id in self.user_queue_info:
                self.user_queue_info[user_id] = queue_info
                self.user_queue_info[user_id]['position'] = new_position
    
    async def notify_download_started(self, user_id: int):
        """Notify that download has started for a user"""
        async with self.lock:
            if user_id in self.user_status_messages:
                message = self.user_status_messages[user_id]
                try:
                    await message.edit_text(
                        "⬇️ **Downloading now...**\n"
                        "Your turn has come! Processing your request.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to update status for user {user_id}: {e}")
    
    async def cleanup_user(self, user_id: int):
        """Clean up user resources after download completes"""
        async with self.lock:
            # Cancel update task
            if user_id in self.update_tasks:
                self.update_tasks[user_id].cancel()
                del self.update_tasks[user_id]
            
            # Remove from tracking (but keep message)
            if user_id in self.user_queue_info:
                del self.user_queue_info[user_id]
    
    async def _update_user_status(self, user_id: int):
        """Periodically update user's queue status"""
        from queue_manager import download_queue
        
        try:
            while True:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                async with self.lock:
                    if user_id not in self.user_status_messages:
                        break
                    
                    message = self.user_status_messages[user_id]
                    queue_info = self.user_queue_info.get(user_id, {})
                    
                    # Get current queue status
                    status = await download_queue.get_queue_status(user_id)
                    
                    if status['status'] == 'queued':
                        position = status['position']
                        active_count = status['active_count']
                        queue_size = status['queue_size']
                        
                        # Update message if position changed
                        if queue_info.get('position') != position:
                            try:
                                await message.edit_text(
                                    f"🎵 **You are in queue**\n"
                                    f"📊 **Position:** #{position}\n"
                                    f"👥 **Ahead of you:** {position - 1} users\n"
                                    f"⚡ **Active downloads:** {active_count}/2\n"
                                    f"⏳ **Estimated wait:** ~{position * 2} minutes",
                                    parse_mode="Markdown"
                                )
                                queue_info['position'] = position
                            except Exception as e:
                                logger.error(f"Failed to update queue position for user {user_id}: {e}")
                    
                    elif status['status'] == 'active':
                        # Download started, stop updates
                        await self.notify_download_started(user_id)
                        break
                    
                    elif status['status'] in ['completed', 'failed', 'not_found']:
                        # Download finished, stop updates
                        break
        
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            logger.error(f"Queue update task error for user {user_id}: {e}")

# Global instance
queue_updater = QueueStatusUpdater()

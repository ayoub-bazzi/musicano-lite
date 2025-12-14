import asyncio
import time
from collections import deque
from typing import Dict, List, Optional, Callable, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class DownloadQueue:
    """
    Manages concurrent downloads with limits for Render Free tier.
    Limits: Max 2 concurrent downloads, 5 max queue size
    """
    
    def __init__(self, max_concurrent: int = 2, max_queue_size: int = 5):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.active_downloads: Dict[int, asyncio.Task] = {}  # user_id -> task
        self.waiting_queue = deque()  # FIFO queue of (user_id, callback, args, kwargs)
        self.queue_positions: Dict[int, int] = {}  # user_id -> position in queue
        self.lock = asyncio.Lock()
        self.completed_downloads: Dict[int, Any] = {}  # user_id -> result
        self.failed_downloads: Dict[int, str] = {}  # user_id -> error message
        
    async def add_to_queue(self, user_id: int, callback: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Add a download request to queue.
        Returns: dict with status, position, or immediate execution
        """
        async with self.lock:
            # Check if user already has active download
            if user_id in self.active_downloads:
                return {
                    "status": "already_active",
                    "message": "You already have a download in progress."
                }
            
            # Check if user is already in queue
            for pos, (queued_user_id, _, _, _) in enumerate(self.waiting_queue):
                if queued_user_id == user_id:
                    return {
                        "status": "already_queued",
                        "position": pos + 1,
                        "message": f"You are already in queue at position {pos + 1}."
                    }
            
            # Check queue size limit
            if len(self.waiting_queue) >= self.max_queue_size:
                return {
                    "status": "queue_full",
                    "message": "Queue is full. Please try again later."
                }
            
            # Check if we can start immediately
            if len(self.active_downloads) < self.max_concurrent:
                # Start download immediately
                task = asyncio.create_task(self._execute_download(user_id, callback, args, kwargs))
                self.active_downloads[user_id] = task
                return {
                    "status": "started",
                    "position": 0,
                    "message": "Download started immediately."
                }
            else:
                # Add to queue
                position = len(self.waiting_queue) + 1
                self.waiting_queue.append((user_id, callback, args, kwargs))
                self.queue_positions[user_id] = position
                return {
                    "status": "queued",
                    "position": position,
                    "message": f"Added to queue at position {position}. Please wait..."
                }
    
    async def _execute_download(self, user_id: int, callback: Callable, args: tuple, kwargs: dict):
        """Execute the download and handle cleanup"""
        try:
            # Notify that download has started
            try:
                from queue_status_updater import queue_updater
                await queue_updater.notify_download_started(user_id)
            except ImportError:
                pass
            
            result = await callback(*args, **kwargs)
            self.completed_downloads[user_id] = result
        except Exception as e:
            logger.error(f"Download failed for user {user_id}: {e}")
            self.failed_downloads[user_id] = str(e)
        finally:
            async with self.lock:
                # Remove from active downloads
                if user_id in self.active_downloads:
                    del self.active_downloads[user_id]
                
                # Clean up status updater
                try:
                    from queue_status_updater import queue_updater
                    await queue_updater.cleanup_user(user_id)
                except ImportError:
                    pass
                
                # Start next download from queue if available
                await self._start_next_download()
    
    async def _start_next_download(self):
        """Start the next download from the queue if slots available"""
        if self.waiting_queue and len(self.active_downloads) < self.max_concurrent:
            user_id, callback, args, kwargs = self.waiting_queue.popleft()
            
            # Update queue positions for remaining users
            for idx, (queued_user_id, _, _, _) in enumerate(self.waiting_queue):
                self.queue_positions[queued_user_id] = idx + 1
            
            # Remove user from queue positions
            if user_id in self.queue_positions:
                del self.queue_positions[user_id]
            
            # Start download
            task = asyncio.create_task(self._execute_download(user_id, callback, args, kwargs))
            self.active_downloads[user_id] = task
    
    async def get_queue_status(self, user_id: int) -> Dict[str, Any]:
        """Get status for a specific user"""
        async with self.lock:
            if user_id in self.active_downloads:
                return {
                    "status": "active",
                    "position": 0,
                    "active_count": len(self.active_downloads),
                    "queue_size": len(self.waiting_queue)
                }
            elif user_id in self.queue_positions:
                position = self.queue_positions[user_id]
                return {
                    "status": "queued",
                    "position": position,
                    "active_count": len(self.active_downloads),
                    "queue_size": len(self.waiting_queue)
                }
            elif user_id in self.completed_downloads:
                return {
                    "status": "completed",
                    "result": self.completed_downloads[user_id]
                }
            elif user_id in self.failed_downloads:
                return {
                    "status": "failed",
                    "error": self.failed_downloads[user_id]
                }
            else:
                return {
                    "status": "not_found",
                    "message": "No download request found."
                }
    
    async def cancel_download(self, user_id: int) -> bool:
        """Cancel a user's download or remove from queue"""
        async with self.lock:
            # Cancel active download
            if user_id in self.active_downloads:
                task = self.active_downloads[user_id]
                task.cancel()
                del self.active_downloads[user_id]
                await self._start_next_download()
                return True
            
            # Remove from queue
            for idx, (queued_user_id, _, _, _) in enumerate(self.waiting_queue):
                if queued_user_id == user_id:
                    self.waiting_queue.remove((queued_user_id, _, _, _))
                    
                    # Update positions
                    for j, (q_user_id, _, _, _) in enumerate(self.waiting_queue):
                        self.queue_positions[q_user_id] = j + 1
                    
                    if user_id in self.queue_positions:
                        del self.queue_positions[user_id]
                    return True
            
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get overall queue statistics"""
        return {
            "active_downloads": len(self.active_downloads),
            "waiting_queue": len(self.waiting_queue),
            "max_concurrent": self.max_concurrent,
            "max_queue_size": self.max_queue_size
        }

# Global queue instance
download_queue = DownloadQueue()

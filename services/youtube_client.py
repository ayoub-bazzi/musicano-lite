import logging
import os
import asyncio
import yt_dlp
import concurrent.futures

logger = logging.getLogger(__name__)

class YouTubeClient:
    def __init__(self):
        # Create a thread pool executor for blocking I/O operations
        # Limited to 2 threads for Render Free tier (0.1 CPU)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    
    async def download_song(self, query, output_path):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'default_search': 'ytsearch',
            'noplaylist': True,
            'cookiefile': 'cookies.txt',
            
            # --- OPTIMIZED FOR FREE TIER ---
            'socket_timeout': 20,  # Reduced from 30
            'retries': 3,          # Reduced from 10
            'fragment_retries': 3, # Reduced from 10
            'ignoreerrors': True,
            
            # --- MEMORY OPTIMIZATION ---
            'buffersize': 1024 * 64,  # Smaller buffer for low memory
            'http_chunk_size': 1048576,  # 1MB chunks
            
            # --- THUMBNAIL LOGIC (BACKUP) ---
            'writethumbnail': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegThumbnailsConvertor', 
                    'format': 'jpg',
                }
            ],
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            # Run download with timeout for free tier constraints
            loop = asyncio.get_event_loop()
            
            # Use thread pool executor to avoid blocking event loop
            download_task = loop.run_in_executor(
                self.executor, 
                self._run_download_with_timeout, 
                ydl_opts, query
            )
            
            # Wait for download with timeout (2 minutes for free tier)
            await asyncio.wait_for(download_task, timeout=120)
            
            # Check for Audio
            final_audio = output_path + ".mp3"
            if not os.path.exists(final_audio) and os.path.exists(output_path):
                final_audio = output_path

            # Check for YouTube Thumbnail (Backup)
            final_thumb = output_path + ".jpg"
            if not os.path.exists(final_thumb):
                final_thumb = None

            if os.path.exists(final_audio):
                logger.info(f"Download successful: {query}")
                return final_audio, final_thumb
            else:
                logger.warning(f"No audio file found for: {query}")
                return None, None
                
        except asyncio.TimeoutError:
            logger.error(f"Download timeout for: {query}")
            raise  # Re-raise to be caught by caller
        except Exception as e:
            logger.error(f"Download Error for '{query}': {e}")
            return None, None

    def _run_download_with_timeout(self, opts, query):
        """Run download with additional timeout handling"""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Extract info first to validate
                info = ydl.extract_info(query, download=False)
                if not info:
                    raise Exception("No video found")
                
                # Then download
                ydl.download([query])
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in download: {e}")
            raise
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

youtube_client = YouTubeClient()

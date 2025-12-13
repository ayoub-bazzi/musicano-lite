import logging
import os
import asyncio
import yt_dlp

logger = logging.getLogger(__name__)

class YouTubeClient:
    def __init__(self):
        pass

    async def download_song(self, query, output_path):
        """
        Downloads a song based on a search query (Artist - Title) using yt-dlp.
        Saves it to output_path.
        """
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'default_search': 'ytsearch',
            'noplaylist': True,
            'cookiefile': 'cookies.txt',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._run_download(ydl_opts, query))
            
            final_path = output_path + ".mp3"
            if os.path.exists(final_path):
                return final_path
            elif os.path.exists(output_path):
                return output_path
                
            return None
        except Exception as e:
            logger.error(f"Download Error for '{query}': {e}")
            return None

    def _run_download(self, opts, query):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([query])

youtube_client = YouTubeClient()
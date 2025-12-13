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
            'outtmpl': output_path,  # Save exactly to this path
            'default_search': 'ytsearch',  # Use YouTube Search
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True
        }

        try:
            # Run blocking yt-dlp code in a separate thread so bot doesn't freeze
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._run_download(ydl_opts, query))
            
            # Since we specified output_path, we check if the file (or the mp3 version) exists
            # yt-dlp might append .mp3 to the filename, so we check for that too.
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
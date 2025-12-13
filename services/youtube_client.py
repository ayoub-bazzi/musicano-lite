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
        Downloads song ONLY (No thumbnail needed, we get it from Spotify).
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'default_search': 'ytsearch',
            'noplaylist': True,
            'cookiefile': 'cookies.txt',
            
            'writethumbnail': False, 
            
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ],
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._run_download(ydl_opts, query))
            
            final_audio = output_path + ".mp3"
            if not os.path.exists(final_audio) and os.path.exists(output_path):
                final_audio = output_path

            if os.path.exists(final_audio):
                return final_audio, None # Return None for thumb since get handle externally
                
            return None, None
        except Exception as e:
            logger.error(f"Download Error for '{query}': {e}")
            return None, None

    def _run_download(self, opts, query):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([query])

youtube_client = YouTubeClient()
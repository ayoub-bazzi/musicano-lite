# services/youtube_client.py
import logging
import os
import asyncio
import sys

logger = logging.getLogger(__name__)

class YouTubeClient:
    def __init__(self):
        pass

    async def download_track(self, spotify_url, output_path):
        """Downloads using the 'spotdl' command line tool via subprocess."""
        try:
            # FIX: Added "force" after "--overwrite"
            cmd = [
                sys.executable, "-m", "spotdl", "download",
                spotify_url,
                "--output", output_path,
                "--format", "m4a",
                "--overwrite", "force"  
            ]

            # Run the command in a separate thread
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for it to finish
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                # Log the error if it failed
                error_msg = stderr.decode().strip() or stdout.decode().strip()
                # Ignore harmless ffmpeg warnings
                if "FFmpeg" in error_msg and os.path.exists(output_path):
                    return output_path
                    
                logger.error(f"SpotDL Failed for {spotify_url}: {error_msg}")
                return None

        except Exception as e:
            logger.error(f"SpotDL Subprocess Error ({spotify_url}): {e}")
            return None

youtube_client = YouTubeClient()
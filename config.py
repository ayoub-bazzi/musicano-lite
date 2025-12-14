import os

BOT_VERSION = "2.1.0"

DB_NAME = "musicano_lite.db"

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not BOT_TOKEN:
    print("⚠️ WARNING: BOT_TOKEN is missing! Make sure you added it in Render Environment Variables.")

import os

# --- Database Configuration ---
DB_NAME = "musicano_lite.db"

# --- API Keys (From Secrets) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# --- Validation ---
if not BOT_TOKEN:
    print("⚠️ WARNING: BOT_TOKEN is missing! Make sure you added it in Render Environment Variables.")
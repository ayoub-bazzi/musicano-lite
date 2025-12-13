# database.py
import sqlite3
from config import DB_NAME

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Stores channel info
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                playlist_link TEXT
            )
        """)
        # Stores the "Mirror" state
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posted_tracks (
                spotify_id TEXT PRIMARY KEY,
                channel_id INTEGER,
                telegram_msg_id INTEGER,
                track_name TEXT
            )
        """)
        conn.commit()

# --- Channel CRUD ---
def add_channel(channel_id, user_id, title, playlist_link):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR REPLACE INTO channels VALUES (?, ?, ?, ?)", 
                     (channel_id, user_id, title, playlist_link))

def get_user_channels(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT * FROM channels WHERE user_id = ?", (user_id,)).fetchall()

def get_channel(channel_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,)).fetchone()

def delete_channel(channel_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.execute("DELETE FROM posted_tracks WHERE channel_id = ?", (channel_id,))

# --- Track CRUD ---
def get_channel_tracks(channel_id):
    """Returns a dictionary: {spotify_id: telegram_msg_id}"""
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute("SELECT spotify_id, telegram_msg_id FROM posted_tracks WHERE channel_id = ?", (channel_id,)).fetchall()
        return {row[0]: row[1] for row in rows}

def add_track(spotify_id, channel_id, msg_id, name):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR REPLACE INTO posted_tracks VALUES (?, ?, ?, ?)", 
                     (spotify_id, channel_id, msg_id, name))

def delete_track(spotify_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM posted_tracks WHERE spotify_id = ?", (spotify_id,))
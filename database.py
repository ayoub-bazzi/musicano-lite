import os
import psycopg2
from urllib.parse import urlparse

# Get DB URL from Render Environment
DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create Channels Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id BIGINT PRIMARY KEY,
                user_id BIGINT,
                title TEXT,
                playlist_link TEXT
            );
        """)
        
        # Create Tracks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posted_tracks (
                spotify_id TEXT PRIMARY KEY,
                channel_id BIGINT,
                telegram_msg_id BIGINT,
                track_name TEXT
            );
        """)
        
        conn.commit()
        conn.close()
        print("✅ Database Initialized (PostgreSQL)")
    except Exception as e:
        print(f"❌ DB Init Error: {e}")

# --- Channel CRUD ---
def add_channel(channel_id, user_id, title, playlist_link):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO channels (channel_id, user_id, title, playlist_link)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (channel_id) DO UPDATE 
            SET playlist_link = EXCLUDED.playlist_link, title = EXCLUDED.title;
        """, (channel_id, user_id, title, playlist_link))
        conn.commit()
    finally:
        conn.close()

def get_user_channels(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM channels WHERE user_id = %s", (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()

def get_channel(channel_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM channels WHERE channel_id = %s", (channel_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def delete_channel(channel_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM channels WHERE channel_id = %s", (channel_id,))
        cursor.execute("DELETE FROM posted_tracks WHERE channel_id = %s", (channel_id,))
        conn.commit()
    finally:
        conn.close()

# --- Track CRUD ---
def get_channel_tracks(channel_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT spotify_id, telegram_msg_id FROM posted_tracks WHERE channel_id = %s", (channel_id,))
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    finally:
        conn.close()

def add_track(spotify_id, channel_id, msg_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO posted_tracks (spotify_id, channel_id, telegram_msg_id, track_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (spotify_id) DO NOTHING;
        """, (spotify_id, channel_id, msg_id, name))
        conn.commit()
    finally:
        conn.close()

def delete_track(spotify_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM posted_tracks WHERE spotify_id = %s", (spotify_id,))
        conn.commit()
    finally:
        conn.close()
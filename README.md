# 🎵 Musicano Lite

![Status](https://img.shields.io/badge/Status-Operational-brightgreen?style=for-the-badge)
![Hosting](https://img.shields.io/badge/Hosting-Render_Free_Tier-purple?style=for-the-badge)
![RAM Usage](https://img.shields.io/badge/RAM_Limit-512MB-red?style=for-the-badge)
[![Bot](https://img.shields.io/badge/Bot-t.me/MusicanoLiteBoti-blue?style=for-the-badge)](https://t.me/MusicanoLiteBot)

> **A high-performance Telegram Music Bot engineered to run on strict resource limits.**

---

## 💡 The Engineering Challenge
Most music bots require expensive VPS hosting because audio processing is heavy. They consume high CPU and RAM, making them impossible to run on free tiers like Render.

**The Goal:** Build a production-ready music bot that survives on **512MB RAM** and **0.1 CPU** cores.
**The Result:** Musicano Lite. A bot that uses architectural optimizations instead of raw power to deliver high-quality audio 24/7.

---

## ⚙️ How It Works (The Architecture)

To bypass hardware limitations, I implemented three core optimizations:

### 1. The "Traffic Controller" Queue System
* **Problem:** Running multiple downloads simultaneously crashes a 512MB server immediately.
* **Solution:** A custom-built `QueueManager` that strictly serializes heavy tasks. Even if 50 users request songs at once, the bot processes them one-by-one. This guarantees RAM usage never spikes above the limit, keeping the bot alive while remaining responsive to commands.

### 2. Smart "Anti-Mashup" Filtering
* **Problem:** `yt-dlp` often grabs 10-minute compilation videos instead of the actual song, wasting bandwidth and time.
* **Solution:** I wrote a custom metadata filter that inspects video duration and titles before downloading.
    * *Rule:* Reject video if > 7 minutes.
    * *Rule:* Reject video if title contains "Compilation", "Mix", or "Full Album".
    * *Result:* The bot delivers the correct track with 99% accuracy.

### 3. Safe-Mode Playlist Sync
* **Problem:** Syncing Spotify playlists to Telegram is risky; API errors can cause the bot to accidentally wipe a user's database.
* **Solution:** A "Safety Lock" protocol. If the Spotify API returns an empty list (a common error), the bot aborts the sync process instantly instead of assuming the playlist is empty.

---

## 🚀 Key Features

* **Universal Downloader:** Converts Spotify Links (Tracks, Playlists) and Search Queries to MP3.
* **Channel Mirroring:** Two-way sync between a Spotify Playlist and a Telegram Channel (Auto-Add/Auto-Remove).
* **High-Quality Audio:** Delivers 192kbps MP3s with full metadata (Cover Art, Artist, Title).
* **Async Core:** Built on `httpx` and `asyncio` to ensure the bot responds to text commands even during heavy processing.
* **24/7 Uptime:** Optimized to work with external ping services (UptimeRobot) to prevent free-tier sleep mode.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Framework:** `python-telegram-bot` (Async)
* **Engine:** `yt-dlp` (Custom configuration)
* **APIs:** Spotify Web API, Telegram Bot API
* **Database:** SQLite (Lightweight & fast)
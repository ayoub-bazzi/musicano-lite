import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

class SpotifyClient:
    def __init__(self):
        try:
            auth_manager = SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            print(f"⚠️ Spotify Auth Error: {e}")
            self.sp = None

    def get_playlist_tracks(self, playlist_url):
        if not self.sp: return []
        try:
            results = self.sp.playlist_items(
                playlist_url, 
                fields="items(track(id,name,artists(name))),next"
            )
            tracks = results['items']
            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])
            
            cleaned_tracks = []
            for item in tracks:
                track = item.get('track')
                if track and track.get('id'): 
                    cleaned_tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': track['artists'][0]['name']
                    })
            return cleaned_tracks
        except Exception as e:
            print(f"Spotify Playlist Error: {e}")
            return []

    # --- NEW: Get Metadata from Link (with Image) ---
    def get_track_info(self, track_url):
        """Returns (query, cover_url, title, artist)"""
        if not self.sp: return None
        try:
            track = self.sp.track(track_url)
            name = track['name']
            artist = track['artists'][0]['name']
            cover_url = track['album']['images'][0]['url'] if track['album']['images'] else None
            
            return (f"{artist} - {name} audio", cover_url, name, artist)
        except Exception as e:
            print(f"Spotify Track Error: {e}")
            return None

    # --- NEW: Search Spotify by Text ---
    def search_track(self, query):
        """Searches Spotify for a song and returns best match."""
        if not self.sp: return None
        try:
            results = self.sp.search(q=query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                name = track['name']
                artist = track['artists'][0]['name']
                cover_url = track['album']['images'][0]['url'] if track['album']['images'] else None
                
                return (f"{artist} - {name} audio", cover_url, name, artist)
            return None
        except Exception as e:
            print(f"Spotify Search Error: {e}")
            return None

spotify_client = SpotifyClient()
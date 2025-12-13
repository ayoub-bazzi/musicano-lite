import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

class SpotifyClient:
    def __init__(self):
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_playlist_tracks(self, playlist_url):
        """Fetches ONLY the ID, Name, and Artist to make verification fast."""
        try:
            # OPTIMIZATION: 'fields' reduces the data size by ~90%
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
                track = item.get('track') # Safety check
                if track and track.get('id'): 
                    cleaned_tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': track['artists'][0]['name']
                    })
            return cleaned_tracks
        except Exception as e:
            print(f"Spotify Error: {e}")
            return []

spotify_client = SpotifyClient()
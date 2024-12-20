import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyManager:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope='user-read-playback-state user-read-currently-playing'
        ))
        self.current_playback = None

    def update_playback(self):
        self.current_playback = self.sp.current_playback()

    def is_ad_playing(self):
        if not self.current_playback:
            return False
        return self.current_playback.get('currently_playing_type') == 'ad'

    def skip_ad(self, system_manager):
        if self.current_playback.get('is_playing'):
            system_manager.play_pause_media()

        system_manager.close_spotify_and_wait()
        system_manager.open_spotify_behind()

    def get_current_playback(self):
        if not self.current_playback:
            return None
        if self.current_playback.get('currently_playing_type') == 'ad':
            return 'Advertisement'

        track = self.current_playback.get('item')
        if not track:
            return None
        name = track.get('name')
        artists = [artist.get('name') for artist in track.get('artists', [])]
        artist_names = ', '.join(filter(None, artists))

        return f"{name} by {artist_names}"

    def get_time_left(self):
        if not self.current_playback:
            return None
        if self.is_ad_playing():
            return None

        track = self.current_playback.get('item')
        if not track:
            return None

        progress_ms = self.current_playback.get('progress_ms')
        duration_ms = track.get('duration_ms')
        if not progress_ms or not duration_ms:
            return None

        time_left_ms = duration_ms - progress_ms
        return time_left_ms

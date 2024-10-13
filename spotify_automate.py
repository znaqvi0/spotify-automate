import os
import time

import requests.exceptions
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from dotenv import load_dotenv

from audio_processing import get_current_audio, is_advertisement_playing, song_time_left
from system_management import prevent_sleep, is_spotify_running, open_spotify, play_pause_media, open_play, \
    wait_until_spotify_closed

load_dotenv()

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')


def authorize(client_id, client_secret, redirect_uri):
    auth_manager = SpotifyOAuth(client_id=client_id,
                                client_secret=client_secret,
                                redirect_uri=redirect_uri,
                                scope='user-read-playback-state user-read-currently-playing')
    return spotipy.Spotify(auth_manager=auth_manager)


def spotify_running_check(result, path):
    if result:
        return
    if not is_spotify_running():
        open_play(path)


def print_time_left(result, time_left):
    left = round(time_left / 1000, 1) if time_left is not None else 'N/A'
    print(get_current_audio(result), f"({left} seconds left)")


def time_check(result, sleep):
    time_left = song_time_left(result)
    print_time_left(result, time_left)
    if not time_left:
        return
    time.sleep(min(sleep, 0.7 * time_left / 1000))


def advertisement_check(result, path):
    if is_advertisement_playing(result):
        if result['is_playing']:
            play_pause_media()
        wait_until_spotify_closed(2)
        open_play(path)
        return True
    return False


def main(sp, path, sleep):
    prevent_sleep()
    result = sp.current_playback()
    time_check(result, sleep)
    if not advertisement_check(result, path):
        spotify_running_check(result, path)


def run_main(client_id, client_secret, redirect_uri, path, sleep):
    sp = authorize(client_id, client_secret, redirect_uri)
    while True:
        main(sp, path, sleep)


spotify_path = 'C:\\Users\\znaqv\\AppData\\Roaming\\Spotify\\Spotify.exe'
sleep_time = 5

redirect_uri = 'http://localhost:8000'


# to recreate the .exe file use command pyinstaller --onefile spotify_automate.py
def run_program():
    try:
        run_main(client_id, client_secret, redirect_uri, spotify_path, sleep_time)
    except KeyboardInterrupt:
        open_spotify(spotify_path)
        os.system(f'taskkill /pid {os.getpid()} /f')
    except requests.exceptions.ReadTimeout:
        print("--------------------\nhandling ReadTimeout\n--------------------")
        run_program()
    except requests.exceptions.ConnectionError:
        print("--------------------\nhandling ConnectionError\n--------------------")
        run_program()


if __name__ == '__main__':
    run_program()

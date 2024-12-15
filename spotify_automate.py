import logging
import os
import time

import requests.exceptions
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from audio_processing import get_current_audio, is_advertisement_playing, song_time_left
from system_management import prevent_sleep, is_spotify_running, play_pause_media, open_play, \
    wait_until_spotify_closed, get_spotify_path, SPOTIFY_CLOSE_TIMEOUT

load_dotenv()

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    logging.info(f"{get_current_audio(result)} ({left} seconds left)")


def time_check(result, sleep_time):
    time_left = song_time_left(result)
    print_time_left(result, time_left)
    if not time_left:
        return
    time.sleep(min(sleep_time, 0.7 * time_left / 1000))


def advertisement_check(result, path):
    if not is_advertisement_playing(result):
        return False

    if result['is_playing']:
        play_pause_media()
    wait_until_spotify_closed(SPOTIFY_CLOSE_TIMEOUT)
    open_play(path)
    return True


def main(sp, path, sleep_time):
    prevent_sleep()
    result = sp.current_playback()
    time_check(result, sleep_time)
    if not advertisement_check(result, path):
        spotify_running_check(result, path)


def run_main(client_id, client_secret, redirect_uri, path, sleep_time):
    sp = authorize(client_id, client_secret, redirect_uri)
    while True:
        main(sp, path, sleep_time)


spotify_path = get_spotify_path()
sleep_time = 5


# to recreate the .exe file use command pyinstaller --onefile spotify_automate.py
def run_program():
    try:
        run_main(client_id, client_secret, REDIRECT_URI, spotify_path, sleep_time)
    except KeyboardInterrupt:
        logging.info("Program interrupted by user. Shutting down...")
        os.system(f'taskkill /pid {os.getpid()} /f')
    except requests.exceptions.ReadTimeout:
        logging.warning("ReadTimeout encountered. Restarting main loop...")
        run_program()
    except requests.exceptions.ConnectionError:
        logging.warning("ConnectionError encountered. Restarting main loop...")
        run_program()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == '__main__':
    run_program()
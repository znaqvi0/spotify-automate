import logging
import os
import time

import requests.exceptions
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from audio_processing import get_current_playback, is_ad_playing, song_time_left
from system_management import SystemManager

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


def spotify_running_check(result, sys_manager):
    if result:
        return
    if not sys_manager.is_spotify_running():
        sys_manager.open_play()


def print_time_left(result, time_left):
    left = round(time_left / 1000, 1) if time_left is not None else 'N/A'
    logging.info(f"{get_current_playback(result)} ({left} seconds left)")


def time_check(result, sleep_time):
    time_left = song_time_left(result)
    print_time_left(result, time_left)
    if not time_left:
        return
    time.sleep(min(sleep_time, 0.7 * time_left / 1000))


def advertisement_check(result, sys_manager):
    if not is_ad_playing(result):
        return False

    if result['is_playing']:
        sys_manager.play_pause_media()
    sys_manager.wait_until_spotify_closed()
    sys_manager.open_play()
    return True


def main(sp, sys_manager, sleep_time):
    sys_manager.prevent_sleep()
    result = sp.current_playback()
    time_check(result, sleep_time)
    if not advertisement_check(result, sys_manager):
        spotify_running_check(result, sys_manager)


def run_main(client_id, client_secret, redirect_uri, sys_manager, sleep_time):
    sp = authorize(client_id, client_secret, redirect_uri)
    while True:
        main(sp, sys_manager, sleep_time)


sleep_time = 5

sys_manager = SystemManager()
# to recreate the .exe file use command pyinstaller --onefile spotify_automate.py
def run_program():
    try:
        run_main(client_id, client_secret, REDIRECT_URI, sys_manager, sleep_time)
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
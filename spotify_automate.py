import logging
import os
import time

import psutil
import requests.exceptions
from dotenv import load_dotenv

from spotify_manager import SpotifyManager
from system_manager import SystemManager

# configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def print_time_left(spotify_manager):
    time_ms = spotify_manager.get_time_left()
    seconds_left = round(time_ms / 1000, 1) if time_ms is not None else 'N/A'
    logging.info(f"{spotify_manager.get_current_playback()} ({seconds_left} seconds left)")


def sleep(spotify_manager, sleep_time):
    time_left = spotify_manager.get_time_left()
    if not time_left:
        return
    time.sleep(min(sleep_time, 0.7 * time_left / 1000))


def main(sleep_interval):
    load_dotenv()
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = 'http://localhost:8000'

    spotify_manager = SpotifyManager(client_id, client_secret, redirect_uri)
    system_manager = SystemManager()

    while True:
        spotify_manager.update_playback()
        system_manager.prevent_sleep()

        if not spotify_manager.current_playback:  # shortcut to checking if spotify is open
            if not system_manager.is_spotify_running():
                system_manager.open_play()

        if spotify_manager.is_ad_playing():
            spotify_manager.skip_ad(system_manager)

        print_time_left(spotify_manager)

        sleep(spotify_manager, sleep_interval)


sleep_time = 5


# to recreate the .exe file use command pyinstaller --onefile spotify_automate.py
def run_program():
    try:
        main(sleep_time)
    except KeyboardInterrupt:
        logging.info("Program interrupted by user. Shutting down...")
        os.system(f'taskkill /pid {os.getpid()} /f')
    except requests.exceptions.ReadTimeout:
        logging.warning("ReadTimeout encountered. Restarting main loop...")
        run_program()
    except requests.exceptions.ConnectionError:
        logging.warning("ConnectionError encountered. Restarting main loop...")
        run_program()
    except psutil.NoSuchProcess:
        logging.warning("NoSuchProcess encountered. Restarting main loop...")
        run_program()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == '__main__':
    run_program()

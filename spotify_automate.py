import asyncio
import os
import subprocess
import time

import pyautogui
import psutil
import requests.exceptions
import spotipy
import win32con
import win32gui
from spotipy.oauth2 import SpotifyOAuth
import ctypes

from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')


ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def authorize(client_id, client_secret, redirect_uri):
    auth_manager = SpotifyOAuth(client_id=client_id,
                                client_secret=client_secret,
                                redirect_uri=redirect_uri,
                                scope='user-read-playback-state user-read-currently-playing')
    return spotipy.Spotify(auth_manager=auth_manager)


def prevent_sleep(es_continuous, es_system_required, es_display_required):
    ctypes.windll.kernel32.SetThreadExecutionState(es_continuous | es_system_required | es_display_required)


def close_spotify():
    # sends a command to the terminal to close spotify.exe
    os.system("taskkill /im spotify.exe")


def force_close_spotify():
    os.system("taskkill /im spotify.exe /f")


def get_current_audio(result):
    if not result:
        return None
    if result['currently_playing_type'] == 'ad':
        return 'Advertisement'

    track = result['item']
    name = track['name']
    artists = [artist['name'] for artist in track['artists']]
    artist_names = ', '.join(artists)

    return f"{name} by {artist_names}"


def is_spotify_running():
    for process in psutil.process_iter():
        if process.name() == 'Spotify.exe':
            return True
    return False


def open_spotify(path):
    subprocess.Popen(path)


def open_spotify_minimized(path):
    # Use the STARTF_USESHOWWINDOW flag to start the process minimized
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # Start the Spotify process
    subprocess.Popen(path, startupinfo=startupinfo)


def is_advertisement_playing(result):
    keyword = "Advertisement"
    current_audio = get_current_audio(result)
    if not current_audio:
        return False

    return keyword in current_audio


def song_time_left(result):
    if not result:
        return None
    # maybe remove/change the condition here
    if not is_advertisement_playing(result):
        progress_ms = result['progress_ms']
        duration_ms = result['item']['duration_ms']
        time_left_ms = duration_ms - progress_ms
        return time_left_ms


def play_pause_media():
    pyautogui.hotkey('playpause')


def open_spotify_behind(path):
    # subprocess.Popen(path, shell=True)
    subprocess.Popen(path)
    # Wait for Spotify window to appear
    while True:
        window = win32gui.FindWindow(None, "Spotify Free")
        if window != 0:
            break
    # Set Spotify window to be behind all other windows
    win32gui.SetWindowPos(window, win32con.HWND_BOTTOM, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


def wait_until_spotify_open(max_time, path):
    initial_time = time.perf_counter()
    open_spotify_behind(path)
    while True:
        time_elapsed = time.perf_counter() - initial_time
        if time_elapsed >= max_time:
            break
        spotify_processes = [proc for proc in psutil.process_iter() if proc.name() == 'Spotify.exe']
        if len(spotify_processes) >= 4:  # change value? original 5
            print(f'spotify opened in %.3f seconds' % time_elapsed)
            break


async def open_play(path):
    wait_until_spotify_open(5, path)
    play_pause_media()


def wait_until_spotify_closed(max_time):
    initial_time = time.perf_counter()
    close_spotify()
    while True:
        current_time = time.perf_counter()
        time_elapsed = current_time - initial_time
        if time_elapsed >= max_time:
            break
        spotify_processes = [proc for proc in psutil.process_iter() if proc.name() == 'Spotify.exe']
        if len(spotify_processes) <= 1:  # change value? original 1
            print(f'spotify closed in {round(time_elapsed * 1000) / 1000} seconds')
            break


async def spotify_running_check(result, path):
    if result:
        return
    if not is_spotify_running():
        await open_play(path)


async def time_check(result, time_left, sleep):
    if not (result and time_left):
        return
    await asyncio.sleep(min(sleep, 0.7 * time_left / 1000))


async def advertisement_check(result, path):
    if is_advertisement_playing(result):
        if result['is_playing']:
            play_pause_media()
        wait_until_spotify_closed(2)
        await open_play(path)
        return True
    return False


async def main(sp, path, sleep):
    result = sp.current_playback()
    if not await advertisement_check(result, path):
        await spotify_running_check(result, path)

        prevent_sleep(ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED)
        time_left = song_time_left(result)
        print(get_current_audio(result),
              f"({round(time_left / 100) / 10 if time_left is not None else 'N/A'} seconds left)")

        await time_check(result, time_left, sleep)


async def run_main(client_id, client_secret, redirect_uri, path, sleep):
    sp = authorize(client_id, client_secret, redirect_uri)
    while True:
        await main(sp, path, sleep)


spotify_path = 'C:\\Users\\znaqv\\AppData\\Roaming\\Spotify\\Spotify.exe'
sleep_time = 5

redirect_uri = 'http://localhost:8000'


# to recreate the .exe file use command pyinstaller --onefile spotify_automate.py
def run_program():
    # Run the main loop using an event loop
    try:
        asyncio.run(run_main(client_id, client_secret, redirect_uri, spotify_path, sleep_time))
    except KeyboardInterrupt:
        open_spotify(spotify_path)
        os.system(f'taskkill /pid {os.getpid()} /f')
    except requests.exceptions.ReadTimeout:
        print("--------------------\nhandling ReadTimeout\n--------------------")
        run_program()
    except requests.exceptions.ConnectionError:
        print("--------------------\nhandling ConnectionError\n--------------------")
        run_program()


run_program()

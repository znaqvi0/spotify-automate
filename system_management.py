import ctypes
import os
import subprocess
import time
import logging

import psutil
import pyautogui
import win32con
import win32gui

# Constants for SetThreadExecutionState
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# Constants for Timeouts
SPOTIFY_OPEN_TIMEOUT = 5
SPOTIFY_CLOSE_TIMEOUT = 2
SPOTIFY_PROCESS_THRESHOLD = 5

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )


def get_spotify_path():
    def is_from_ms_store():
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-AppxPackage *Spotify*'],
                capture_output=True,
                text=True,
                check=True,
            )
            return 'SpotifyAB.SpotifyMusic' in result.stdout
        except subprocess.CalledProcessError as e:
            logging.error(f'Error getting AppxPackage: {e}')
            return False

    username = os.getlogin()
    appdata_path = f'C:\\Users\\{username}\\AppData\\Roaming\\Spotify\\Spotify.exe'
    microsoft_store_path = ['start', 'spotify:']

    if os.path.exists(appdata_path):
        return [appdata_path]
    if is_from_ms_store():
        return microsoft_store_path
    raise FileNotFoundError('Spotify.exe not found')


def close_spotify():
    try:
        os.system('taskkill /im spotify.exe')
    except Exception as e:
        logging.error(f'Error closing Spotify: {e}')


def is_spotify_running():
    return any(proc.name() == 'Spotify.exe' for proc in psutil.process_iter())


def open_spotify(path):
    subprocess.Popen(path, shell='start' in path)


def play_pause_media():
    pyautogui.hotkey('playpause')


def open_spotify_behind(path):
    open_spotify(path)
    # Wait for Spotify window to appear
    start_time = time.perf_counter()
    window = None
    while time.perf_counter() - start_time < SPOTIFY_OPEN_TIMEOUT:
        window = win32gui.FindWindow(None, 'Spotify Free')
        if window:
            break

    if window:
        # Set Spotify window to be behind all other windows
        win32gui.SetWindowPos(
            window, win32con.HWND_BOTTOM, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
    else:
        logging.warning('Spotify window not found within timeout')


def wait_until_spotify_open(max_time, path):
    initial_time = time.perf_counter()
    open_spotify_behind(path)
    while True:
        time_elapsed = time.perf_counter() - initial_time
        if time_elapsed >= max_time:
            break
        spotify_processes = [proc for proc in psutil.process_iter() if proc.name() == 'Spotify.exe']

        if len(spotify_processes) >= SPOTIFY_PROCESS_THRESHOLD:
            logging.info(f'spotify opened in %.3f seconds' % time_elapsed)
            break


def open_play(path):
    wait_until_spotify_open(SPOTIFY_OPEN_TIMEOUT, path)
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
        if len(spotify_processes) <= 1:
            logging.info(f'spotify closed in {round(time_elapsed, 3)} seconds')
            break
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

class SystemManager:
    def __init__(self):
        self.spotify_path = self.get_spotify_path()

    @staticmethod
    def prevent_sleep():
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )

    @staticmethod
    def is_spotify_running():
        return any(proc.name() == 'Spotify.exe' for proc in psutil.process_iter())

    def open_spotify(self):
        subprocess.Popen(self.spotify_path, shell='start' in self.spotify_path)

    def open_spotify_behind(self):
        self.open_spotify()
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

    @staticmethod
    def close_spotify():
        try:
            os.system('taskkill /im spotify.exe')
        except Exception as e:
            logging.error(f'Error closing Spotify: {e}')

    @staticmethod
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

    def wait_until_spotify_open(self):
        start_time = time.perf_counter()
        self.open_spotify_behind()
        while time.perf_counter() - start_time < SPOTIFY_OPEN_TIMEOUT:
            if self.is_spotify_running():
                logging.info(f'spotify opened in %.3f seconds' % (time.perf_counter() - start_time))
                break

        if not self.is_spotify_running():
            logging.warning('Spotify failed to open within timeout')

    def wait_until_spotify_closed(self):
        start_time = time.perf_counter()
        self.close_spotify()
        while time.perf_counter() - start_time < SPOTIFY_CLOSE_TIMEOUT:
            if not self.is_spotify_running():
                logging.info(f'spotify closed in %.3f seconds' % (time.perf_counter() - start_time))
                break

        if self.is_spotify_running():
            logging.warning('Spotify failed to close within timeout')

    @staticmethod
    def play_pause_media():
        pyautogui.hotkey('playpause')

    def open_play(self):
        self.wait_until_spotify_open()
        self.play_pause_media()

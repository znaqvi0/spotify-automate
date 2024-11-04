import ctypes
import os
import subprocess
import time

import psutil
import pyautogui
import win32con
import win32gui


def prevent_sleep():
    es_continuous = 0x80000000
    es_system_required = 0x00000001
    es_display_required = 0x00000002
    ctypes.windll.kernel32.SetThreadExecutionState(es_continuous | es_system_required | es_display_required)


def get_spotify_path():
    def is_from_ms_store():
        result = subprocess.run(["powershell", "-Command", "Get-AppxPackage *Spotify*"], capture_output=True,
                                text=True, check=True)
        return 'SpotifyAB.SpotifyMusic' in result.stdout

    username = os.getlogin()
    appdata_path = f'C:\\Users\\{username}\\AppData\\Roaming\\Spotify\\Spotify.exe'
    microsoft_store_path = ['start', 'spotify:']

    if os.path.exists(appdata_path):
        return [appdata_path]
    if is_from_ms_store():
        return microsoft_store_path
    raise FileNotFoundError('Spotify.exe not found')


def close_spotify():
    os.system("taskkill /im spotify.exe")


def is_spotify_running():
    process_names = map(lambda proc: proc.name(), psutil.process_iter())
    return 'Spotify.exe' in process_names


def open_spotify(path):
    subprocess.Popen(path, shell='start' in path)


def play_pause_media():
    pyautogui.hotkey('playpause')


def open_spotify_behind(path):
    open_spotify(path)
    # Wait for Spotify window to appear
    while True:
        window = win32gui.FindWindow(None, "Spotify Free")
        if window:
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
        if len(spotify_processes) >= 4:  # original 5
            print(f'spotify opened in %.3f seconds' % time_elapsed)
            break


def open_play(path):
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
        if len(spotify_processes) <= 1:
            print(f'spotify closed in {round(time_elapsed, 3)} seconds')
            break

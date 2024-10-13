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


def close_spotify():
    os.system("taskkill /im spotify.exe")


def is_spotify_running():
    process_names = map(lambda proc: proc.name(), psutil.process_iter())
    return 'Spotify.exe' in process_names


def open_spotify(path):
    subprocess.Popen(path)


def play_pause_media():
    pyautogui.hotkey('playpause')


def open_spotify_behind(path):
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

import asyncio
import os
import subprocess
import pyautogui
import psutil
import spotipy
import win32con
import win32gui
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import ctypes

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def authorize(client_id, client_secret, redirect_uri):
    # Authenticate with Spotify
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    # Set up authentication and authorization
    auth_manager = SpotifyOAuth(client_id=client_id,
                                client_secret=client_secret,
                                redirect_uri=redirect_uri,
                                scope='user-read-playback-state user-read-currently-playing')
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


def prevent_sleep(ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED):
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)


def close_spotify():
    # sends a command to the terminal to close spotify.exe
    os.system("taskkill /im spotify.exe")


def force_close_spotify():
    os.system("taskkill /im spotify.exe /f")


def get_current_audio(result):
    if result is not None:
        if result['currently_playing_type'] == 'ad':
            return "Advertisement"
    else:
        return None

    track = result['item']
    name = track['name']
    artists = [artist['name'] for artist in track['artists']]
    artist_names = ', '.join(artists)

    return f"{name} by {artist_names}"


def is_spotify_running():
    for process in psutil.process_iter(['name']):
        if process.info['name'] == 'Spotify.exe':
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
    if current_audio is not None:
        if keyword in current_audio:
            return True
    return False


def song_time_left(result):
    if result is not None:
        # maybe remove/change the condition here
        if not is_advertisement_playing(result):
            progress_ms = result['progress_ms']
            duration_ms = result['item']['duration_ms']
            time_left_ms = duration_ms - progress_ms
            return time_left_ms
        else:
            return None
    else:
        return None


def play_pause_media():
    pyautogui.hotkey('playpause')


def open_spotify_behind(path):
    # Open Spotify app
    subprocess.Popen(path, shell=True)

    # Wait for Spotify window to appear
    while True:
        window = win32gui.FindWindow(None, "Spotify Free")
        if window != 0:
            break

    # Set Spotify window to be behind all other windows
    win32gui.SetWindowPos(window, win32con.HWND_BOTTOM, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


async def open_play(path):
    # add afk parameter to open_play and main to determine which opening function should be used?
    open_spotify_minimized(path)
    await asyncio.sleep(2.8)
    play_pause_media()


def is_spotify_responding():
    for proc in psutil.process_iter():
        if proc.name() == 'Spotify.exe':
            return not proc.status() == psutil.STATUS_STOPPED
    return False


def force_close_spotify_if_not_responding():
    spotify_processes = [proc for proc in psutil.process_iter() if proc.name() == 'Spotify.exe']
    if len(spotify_processes) == 1:
        spotify_processes[0].kill()
        return True
    return False


async def main(sp, path, sleep_time):
    result = sp.current_playback()
    time_left = song_time_left(result)
    prevent_sleep(ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED)

    print(get_current_audio(result), f"({round(time_left/100)/10 if time_left is not None else 'N/A'} seconds left)")

    if is_advertisement_playing(result):
        close_spotify()
        await asyncio.sleep(0.75)
        await open_play(path)
    # if check for result is None is removed, can make spotify running check asynchronous
    if result is None:
        if not is_spotify_running():
            await open_play(path)

        # spotify might stop responding because it is hidden for a long time?
        if force_close_spotify_if_not_responding():
            await asyncio.sleep(1.5)
            await open_play(path)

    if result is not None:
        if time_left is not None:
            if time_left > sleep_time * 1000:
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(0.6 * time_left / 1000)


async def run_main_loop(client_id, client_secret, redirect_uri, path, sleep_time):
    sp = authorize(client_id, client_secret, redirect_uri)
    while True:
        await main(sp, path, sleep_time)


# maybe make it so that is_spotify_running is still checked constantly (more async delays?)
spotify_path = "C:\\Users\\znaqv\\AppData\\Roaming\\Spotify\\Spotify.exe"
sleep_time = 5

client_id = '84d3b72b81314414b654d2802866c7cd'
client_secret = '369233c5cc804bf48d9bfad794d9ab6b'
redirect_uri = 'http://localhost:8000'

# Run the main loop using an event loop
asyncio.run(run_main_loop(client_id, client_secret, redirect_uri, spotify_path, sleep_time))

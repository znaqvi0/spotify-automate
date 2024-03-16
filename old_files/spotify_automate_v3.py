import time
import os
import subprocess
import pyautogui
import psutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import ctypes

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

spotify_path = "C:\\Users\\znaqv\\AppData\\Roaming\\Spotify\\Spotify.exe"
play_button_coordinates = 970, 950

client_id = '84d3b72b81314414b654d2802866c7cd'
client_secret = '369233c5cc804bf48d9bfad794d9ab6b'
redirect_uri = 'http://localhost:8000'

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

def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)

def close_spotify():
    # sends a command to the terminal to close spotify.exe
    os.system("taskkill /im spotify.exe")

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

def open_spotify(spotify_path):
    subprocess.Popen(spotify_path)

def open_spotify_minimized(spotify_path):
    # Use the STARTF_USESHOWWINDOW flag to start the process minimized
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # Start the Spotify process
    subprocess.Popen(spotify_path, startupinfo=startupinfo)

def play_music(play_button_coordinates):
    pyautogui.click(play_button_coordinates)

def play_pause(sp):
    # Get the current playback state
    result = sp.current_playback()
    if result is None:
        return

    is_playing = result['is_playing']
    # Play or pause the music depending on the current state
    if is_playing:
        sp.pause_playback()
    else:
        sp.start_playback()

def switch_from_spotify():
    pyautogui.hotkey('alt', 'tab')

def is_advertisement_playing(result):
    keywords = {"Advertisement"}
    current_audio = get_current_audio(result)
    if current_audio != None and current_audio != "Spotify Free":
        for word in keywords:
            if word in current_audio:
                return True
    return False

def main(client_id, client_secret, redirect_uri, spotify_path, play_button_coordinates):
    sp = authorize(client_id, client_secret, redirect_uri)
    result = sp.current_playback()
    print(get_current_audio(result), is_advertisement_playing(result))
    prevent_sleep()
    if(is_advertisement_playing(result)):
        close_spotify()
    if result == None:
        if not is_spotify_running():
            open_spotify_minimized(spotify_path)
            time.sleep(3)
            open_spotify(spotify_path)
            time.sleep(0.3)
            play_music(play_button_coordinates)
            switch_from_spotify()

while True:
    main(client_id, client_secret, redirect_uri, spotify_path, play_button_coordinates)

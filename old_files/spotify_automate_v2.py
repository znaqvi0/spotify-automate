import time
import subprocess
import pyautogui
import keyboard
import pygetwindow as gw

import win32gui
import win32process
import win32con
import psutil

import os
import tkinter as tk

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

def authorize():
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
    output = subprocess.check_output('tasklist', shell=True).decode()
    return 'Spotify.exe' in output

def open_spotify():
    subprocess.Popen(spotify_path)
    # Replace with the path to your Spotify executable
    # Use the STARTF_USESHOWWINDOW flag to start the process minimized
    # startupinfo = subprocess.STARTUPINFO()
    # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # startupinfo.wShowWindow = win32con.SW_MINIMIZE
    # # Start the Spotify process
    # subprocess.Popen(spotify_path, startupinfo=startupinfo)

def open_spotify_minimized():
    # Use the STARTF_USESHOWWINDOW flag to start the process minimized
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # startupinfo.wShowWindow = subprocess.SW_HIDE
    # Start the Spotify process
    subprocess.Popen(spotify_path, startupinfo=startupinfo)

def play_music():
    # Add delay to ensure Spotify is fully loaded
    # time.sleep(3.3)
    # must pass in the correct coordinates of the play button
    pyautogui.click(play_button_coordinates)

def play_pause():
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
    keywords = {"Advertisement",
                # "Sponsored",
                # "Spotify",
                # "Fathom Events",
                # "University",
                # "Waterflame",
                # "Zeiders",
                # "Menzel"
                }
    current_audio = get_current_audio(result)
    if current_audio != None and current_audio != "Spotify Free":
        for word in keywords:
            if word in current_audio:
                return True
    return False

def main():
    global sp
    sp = authorize()
    result = sp.current_playback()
    print(get_current_audio(result), is_advertisement_playing(result))
    prevent_sleep()
    if(is_advertisement_playing(result)):
        close_spotify()
    if not is_spotify_running():
        open_spotify_minimized()
        # wait for spotify to open
        time.sleep(3)
        open_spotify()
        time.sleep(0.3)
        play_music()
        switch_from_spotify()

while True:
    main()

import time
import subprocess
import pyautogui
import keyboard
import pygetwindow as gw

import win32gui
import win32process
import psutil

import os
import tkinter as tk

import ctypes

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

spotify_path = "C:\\Users\\znaqv\\AppData\\Roaming\\Spotify\\Spotify.exe"
play_button_coordinates = 970, 950


def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)


def close_spotify():
    # sends a command to the terminal to close spotify.exe
    os.system("taskkill /im spotify.exe")


def get_current_audio():
    # hwnd = window handle, hwnds = list of window handles
    def callback(hwnd, hwnds):
        # gets the process id of the window if it is visible
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                # adds process to hwnds if the process is spotify.exe
                if process.name() == "Spotify.exe":
                    hwnds.append(hwnd)
            # don't do anything if there is no such process
            except psutil.NoSuchProcess:
                pass
        return True

    hwnds = []
    # list each window
    win32gui.EnumWindows(callback, hwnds)
    if hwnds:
        return win32gui.GetWindowText(hwnds[0])
    else:
        return None


def is_spotify_running():
    output = subprocess.check_output('tasklist', shell=True).decode()
    return 'Spotify.exe' in output


def open_spotify(spotify_path):
    subprocess.Popen(spotify_path)


def open_spotify_minimized(spotify_path):
    # Use the STARTF_USESHOWWINDOW flag to start the process minimized
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # Start the Spotify process
    subprocess.Popen(spotify_path, startupinfo=startupinfo)


def play_music():
    # must pass in the correct coordinates of the play button
    pyautogui.click(play_button_coordinates)


def pause_music():
    open_spotify()
    time.sleep(1)
    # must find the coordinates of the play button
    pyautogui.click(play_button_coordinates)


def switch_from_spotify():
    pyautogui.hotkey('alt', 'tab')


def is_advertisement_playing(current_audio):
    keywords = ["Advertisement",
                "Sponsored",
                "Spotify",
                "Fathom Events",
                "University",
                "Waterflame",
                "Zeiders",
                "Menzel",
                "NO HARD FEELINGS"]
    for word in keywords:
        if current_audio != None:
            if current_audio != "Spotify Free":
                if word in current_audio:
                    return True
    return False


def open_play_switch(spotify_path):
    open_spotify_minimized(spotify_path)
    time.sleep(3)
    open_spotify(spotify_path)
    time.sleep(0.3)
    play_music()
    switch_from_spotify()


def main():
    # print(is_advertisement_playing())
    result = get_current_audio()
    print(result, is_advertisement_playing(result))
    prevent_sleep()
    if (is_advertisement_playing(result)):
        close_spotify()
    if result == None:
        if not is_spotify_running():
            open_play_switch(spotify_path)
    time.sleep(0.2)


while True:
    main()

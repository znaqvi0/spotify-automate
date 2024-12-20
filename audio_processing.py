def get_current_playback(result):
    if not result:
        return None
    if result.get('currently_playing_type') == 'ad':
        return 'Advertisement'

    track = result.get('item')
    if not track:
        return None
    name = track.get('name')
    artists = [artist.get('name') for artist in track.get('artists', [])]
    artist_names = ', '.join(filter(None, artists))

    return f"{name} by {artist_names}"


def is_ad_playing(result):
    if not result:
        return False
    return result.get('currently_playing_type') == 'ad'


def song_time_left(result):
    if not result:
        return None
    if is_ad_playing(result):
        return None

    track = result.get('item')
    if not track:
        return None

    progress_ms = result.get('progress_ms')
    duration_ms = track.get('duration_ms')
    if not progress_ms or not duration_ms:
        return None

    time_left_ms = duration_ms - progress_ms
    return time_left_ms
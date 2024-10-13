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


def is_advertisement_playing(result):
    keyword = "Advertisement"
    current_audio = get_current_audio(result)
    if not current_audio:
        return False

    return keyword in current_audio


def song_time_left(result):
    if not result:
        return None
    if is_advertisement_playing(result):
        return None

    progress_ms = result['progress_ms']
    duration_ms = result['item']['duration_ms']
    time_left_ms = duration_ms - progress_ms
    return time_left_ms

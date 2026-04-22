def analyze_playlist(playlist_id: str):
    songs = get_playlist_songs(playlist_id)
    return {
        "genre_mix": Counter(s.genre for s in songs),
        "tempo_range": (min(s.tempo), max(s.tempo)),
        "average_energy": mean(s.energy)
    }

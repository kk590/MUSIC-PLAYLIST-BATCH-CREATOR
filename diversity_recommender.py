# recommender.py
def recommend_underused(user_id: str, top_n: int = 20):
    all_songs = get_user_library_songs(user_id)
    play_counts = get_play_counts(user_id, all_songs, window_days=90)
    # Compute z-score of play count for each song
    mean_plays = np.mean(play_counts)
    std_plays = np.std(play_counts)
    underused = [
        song for song, count in zip(all_songs, play_counts)
        if (count - mean_plays) / std_plays < -1.0
    ]
    # Sort by popularity outside user's library (optional)
    return underused[:top_n]

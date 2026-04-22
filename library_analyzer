def suggest_groupings(user_id: str):
    songs = await get_all_songs(user_id)
    clusters = perform_clustering(songs, features=['genre', 'tempo', 'key'])
    return format_clusters_as_playlist_suggestions(clusters)

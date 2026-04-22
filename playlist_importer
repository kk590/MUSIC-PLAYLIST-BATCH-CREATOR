@router.post("/playlists/import/spotify")
async def import_spotify(spotify_playlist_id: str):
    tracks = await fetch_spotify_playlist_tracks(spotify_playlist_id)
    # Match with local library or create placeholder songs
    return await create_local_playlist_from_tracks(tracks)

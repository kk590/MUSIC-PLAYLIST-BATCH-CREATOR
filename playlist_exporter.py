# playlist_exporter.py
from typing import Literal
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse, Response

from .models import Playlist, Song
from .exporters import generate_csv, generate_m3u, export_to_spotify

router = APIRouter(prefix="/playlists", tags=["playlist_exporter"])


@router.get("/{playlist_id}/export")
async def export_playlist(playlist_id: str, format: Literal["spotify", "csv", "m3u"]):
    playlist = await Playlist.get_or_none(id=playlist_id)
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    songs = await playlist.songs.all()

    if format == "csv":
        return StreamingResponse(generate_csv(songs), media_type="text/csv")
    if format == "m3u":
        return Response(content=generate_m3u(songs), media_type="audio/x-mpegurl")
    if format == "spotify":
        url = await export_to_spotify(playlist, songs)
        return {"spotify_url": url}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported format")

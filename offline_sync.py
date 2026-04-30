# offline_sync.py
from fastapi import APIRouter, Depends
from .dependencies import get_current_user
from .models import Playlist, Song, User

router = APIRouter(prefix="/playlists", tags=["offline_sync"])


@router.get("/offline-package")
async def offline_package(current_user: User = Depends(get_current_user)):
    playlists = await Playlist.filter(user_id=current_user.id).prefetch_related("songs")
    result = []
    for pl in playlists:
        songs = await pl.songs.all()
        result.append(
            {
                "id": str(pl.id),
                "name": pl.name,
                "songs": [
                    {
                        "id": str(s.id),
                        "title": s.title,
                        "artist": s.artist,
                        "duration": s.duration_seconds,
                    }
                    for s in songs
                ],
            }
        )
    return {"playlists": result}

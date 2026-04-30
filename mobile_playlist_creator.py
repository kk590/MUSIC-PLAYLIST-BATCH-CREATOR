# mobile_playlist_creator.py
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .dependencies import get_current_user
from .models import Playlist, Song, User

router = APIRouter(prefix="/playlists", tags=["mobile_playlist_creator"])


class MobilePlaylistIn(BaseModel):
    name: str
    song_ids: List[str]


@router.post("")
async def create_playlist_mobile(
    payload: MobilePlaylistIn,
    current_user: User = Depends(get_current_user),
):
    playlist = await Playlist.create(user_id=current_user.id, name=payload.name)
    songs = await Song.filter(id__in=payload.song_ids, user_id=current_user.id)
    await playlist.songs.add(*songs)
    return {"playlist_id": playlist.id, "song_count": len(songs)}

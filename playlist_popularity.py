# playlist_popularity.py
from fastapi import APIRouter, Depends
from tortoise.functions import Count

from .dependencies import get_current_user
from .models import PlaylistPlayEvent, User

router = APIRouter(prefix="/playlists", tags=["playlist_popularity"])


@router.get("/popular")
async def popular_playlists(current_user: User = Depends(get_current_user)):
    result = (
        await PlaylistPlayEvent.filter(user_id=current_user.id)
        .values("playlist_id")
        .annotate(plays=Count("id"))
        .order_by("-plays")[:10]
    )
    return result

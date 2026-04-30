# library_stats.py
from fastapi import APIRouter, Depends
from tortoise.functions import Count

from .dependencies import get_current_user
from .models import Song, User

router = APIRouter(prefix="/library", tags=["library_stats"])


@router.get("/stats")
async def library_stats(current_user: User = Depends(get_current_user)):
    total = await Song.filter(user_id=current_user.id).count()
    genre_dist = (
        await Song.filter(user_id=current_user.id)
        .annotate(count=Count("id"))
        .group_by("genre")
        .values("genre", "count")
    )
    return {"total_songs": total, "genres": genre_dist}

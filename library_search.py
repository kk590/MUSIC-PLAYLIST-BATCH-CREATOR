# library_search.py
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from tortoise.expressions import Q

from .dependencies import get_current_user
from .models import Song, User

router = APIRouter(prefix="/songs", tags=["library_search"])


@router.get("/search", response_model=List[Song])
async def search_songs(
    q: Optional[str] = Query(default=None),
    genre: Optional[str] = Query(default=None),
    mood: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    query = Song.filter(user_id=current_user.id)

    if q:
        query = query.filter(Q(title__icontains=q) | Q(artist__icontains=q))
    if genre:
        query = query.filter(genre=genre)
    if mood:
        query = query.filter(mood=mood)

    return await query.limit(50)

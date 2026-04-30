# metadata_editor.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from uuid import UUID

from .dependencies import get_current_user
from .models import Song, User
from .tasks import rewrite_file_tags_task

router = APIRouter(prefix="/songs", tags=["metadata_editor"])


class SongMetadataUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None


@router.patch("/{song_id}/metadata")
async def edit_metadata(
    song_id: UUID,
    metadata: SongMetadataUpdate,
    current_user: User = Depends(get_current_user),
):
    song = await Song.get_or_none(id=song_id, user_id=current_user.id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    update_data = metadata.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(song, k, v)
    await song.save()

    # Background task to rewrite ID3 tags
    if song.file_path:
        rewrite_file_tags_task.delay(song.file_path, update_data)

    return song

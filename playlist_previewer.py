# playlist_previewer.py
from fastapi import APIRouter, HTTPException, status
from .cache import get_generated_playlist_preview

router = APIRouter(prefix="/playlists", tags=["playlist_previewer"])


@router.get("/preview/{job_id}")
async def preview_playlist(job_id: str):
    preview_data = await get_generated_playlist_preview(job_id)
    if not preview_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview not found")

    return {
        "name": preview_data.name,
        "song_count": len(preview_data.songs),
        "sample_songs": preview_data.songs[:10],
    }

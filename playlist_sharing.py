# playlist_sharing.py
import secrets
import io
import base64

import qrcode
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from .models import Playlist, ShareToken

router = APIRouter(prefix="/playlists", tags=["playlist_sharing"])


@router.post("/{playlist_id}/share")
async def generate_share_link(playlist_id: str):
    playlist = await Playlist.get_or_none(id=playlist_id)
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    token = secrets.token_urlsafe(16)
    share_token = await ShareToken.create(
        playlist_id=playlist_id,
        token=token,
        expires_days=30,
    )

    url = f"https://app.com/shared/{token}"

    qr = qrcode.make(url)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    qr_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    qr_data_uri = f"data:image/png;base64,{qr_b64}"

    return JSONResponse(
        {
            "link": f"/shared/{token}",
            "qr": qr_data_uri,
        }
    )

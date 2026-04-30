# mood_playlist_generator.py
from fastapi import APIRouter, Depends, HTTPException, status
from .dependencies import get_current_user
from .models import User, Song, Playlist
from .audio_features import filter_songs_by_audio_features

router = APIRouter(prefix="/mood-playlists", tags=["mood_playlist_generator"])

MOOD_FEATURES = {
    "workout": {"tempo": (120, 180), "energy": (0.7, 1.0)},
    "study": {"tempo": (60, 100), "energy": (0.2, 0.5)},
}


@router.post("/{mood}")
async def generate_for_mood(mood: str, current_user: User = Depends(get_current_user)):
    if mood not in MOOD_FEATURES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported mood")

    features = MOOD_FEATURES[mood]
    songs = await filter_songs_by_audio_features(current_user.id, features)
    playlist = await Playlist.create(
        user_id=current_user.id,
        name=f"{mood.capitalize()} Mix",
    )
    await playlist.songs.add(*songs)

    return {"playlist_id": playlist.id, "song_count": len(songs)}

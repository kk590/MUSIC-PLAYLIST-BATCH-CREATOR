# library_categorizer.py
from fastapi import APIRouter, Depends
from .dependencies import get_current_user
from .models import Song, User
from .audio_features import analyze_audio_features, predict_mood

router = APIRouter(prefix="/library", tags=["library_categorizer"])


class CategoryService:
    async def assign_categories(self, song_id: str):
        song = await Song.get_or_none(id=song_id)
        if not song:
            return

        features = await analyze_audio_features(song)
        categories = {
            "mood": predict_mood(features),
            "tempo": features.get("tempo_bpm"),
            "energy": features.get("energy"),
        }
        song.mood = categories["mood"]
        song.tempo_bpm = categories["tempo"]
        song.energy = categories["energy"]
        await song.save()
        return categories


@router.post("/songs/{song_id}/categorize")
async def categorize_song(song_id: str, current_user: User = Depends(get_current_user)):
    service = CategoryService()
    result = await service.assign_categories(song_id)
    return {"song_id": song_id, "categories": result}

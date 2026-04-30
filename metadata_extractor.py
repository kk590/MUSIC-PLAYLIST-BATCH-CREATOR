# metadata_extractor.py
from celery import shared_task
import mutagen
from mutagen import File as MutagenFile

from .models import Song, User
from .db import db_session


@shared_task(name="extract_metadata_task")
def extract_metadata_task(file_path: str, user_id: str, job_id: str | None = None):
    audio = MutagenFile(file_path)
    if audio is None:
        metadata = {
            "title": "Unknown",
            "artist": "Unknown",
            "album": "",
            "genre": "",
            "duration": 0,
        }
    else:
        metadata = {
            "title": getattr(audio.tags.get("TIT2"), "text", ["Unknown"])[0] if audio.tags and "TIT2" in audio else "Unknown",
            "artist": getattr(audio.tags.get("TPE1"), "text", ["Unknown"])[0] if audio.tags and "TPE1" in audio else "Unknown",
            "album": getattr(audio.tags.get("TALB"), "text", [""])[0] if audio.tags and "TALB" in audio else "",
            "genre": getattr(audio.tags.get("TCON"), "text", [""])[0] if audio.tags and "TCON" in audio else "",
            "duration": int(audio.info.length) if audio.info and hasattr(audio.info, "length") else 0,
        }

    with db_session() as session:
        song = Song(
            user_id=user_id,
            file_path=file_path,
            title=metadata["title"],
            artist=metadata["artist"],
            album=metadata["album"],
            genre=metadata["genre"],
            duration_seconds=metadata["duration"],
        )
        session.add(song)
        session.commit()
    return metadata

# batch_filter_applier.py
from typing import Dict
from tortoise.queryset import QuerySet

from .models import Song


def apply_filters(song_queryset: QuerySet[Song], filters: Dict) -> QuerySet[Song]:
    if "exclude_genres" in filters:
        song_queryset = song_queryset.exclude(genre__in=filters["exclude_genres"])

    # Example implementation for max_artist_occurrences
    max_occ = filters.get("max_artist_occurrences")
    if max_occ is not None:
        # This is a simple in-memory post-processing; for large sets you’d do it in SQL
        async def limited():
            result = []
            counts = {}
            async for song in song_queryset:
                counts[song.artist] = counts.get(song.artist, 0) + 1
                if counts[song.artist] <= max_occ:
                    result.append(song)
            return result

        # caller should await limited() to get the filtered list
        return limited()  # type: ignore

    return song_queryset

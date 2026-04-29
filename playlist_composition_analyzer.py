"""Playlist Composition Analyzer Module

This module provides detailed analysis of playlist composition,
including genre distribution, tempo range, energy levels, and other
musical characteristics.

Technologies: pandas for quick statistics.
"""

from collections import Counter
from typing import Dict, List, Optional
from dataclasses import dataclass
import statistics

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@dataclass
class PlaylistAnalysis:
    """Data class for holding playlist analysis results."""
    playlist_id: str
    playlist_name: str
    total_songs: int
    genre_mix: Dict[str, int]
    tempo_range: tuple
    average_energy: float
    key_distribution: Dict[str, int]
    artist_diversity: float
    duration_minutes: float


class PlaylistCompositionAnalyzer:
    """Analyzes the composition and characteristics of playlists."""

    def __init__(self, song_service=None):
        """
        Args:
            song_service: Service for fetching song data.
                         If None, uses default database queries.
        """
        self.song_service = song_service

    async def analyze_playlist(self, playlist_id: str) -> Dict:
        """Analyze a playlist's composition.

        Args:
            playlist_id: The ID of the playlist to analyze.

        Returns:
            Dictionary containing analysis results.
        """
        songs = await self._get_playlist_songs(playlist_id)

        if not songs:
            return {"error": "Playlist not found or empty"}

        genre_mix = Counter(s.genre for s in songs)
        tempos = [s.tempo for s in songs if s.tempo]
        energies = [s.energy for s in songs if s.energy]
        keys = [s.key for s in songs if s.key]
        artists = [s.artist for s in songs if s.artist]
        durations = [s.duration for s in songs if s.duration]

        return {
            "playlist_id": playlist_id,
            "total_songs": len(songs),
            "genre_mix": dict(genre_mix),
            "tempo_range": (min(tempos), max(tempos)) if tempos else (0, 0),
            "average_tempo": statistics.mean(tempos) if tempos else 0,
            "average_energy": statistics.mean(energies) if energies else 0,
            "key_distribution": dict(Counter(keys)),
            "artist_diversity": len(set(artists)) / len(artists) if artists else 0,
            "total_duration_minutes": sum(durations) / 60 if durations else 0,
            "most_common_genre": genre_mix.most_common(1)[0] if genre_mix else None,
            "tempo_variance": statistics.variance(tempos) if len(tempos) > 1 else 0
        }

    async def _get_playlist_songs(self, playlist_id: str):
        """Fetch songs belonging to a playlist."""
        if self.song_service:
            return await self.song_service.get_playlist_songs(playlist_id)

        # Fallback to ORM query (using Tortoise ORM as per project convention)
        from models import PlaylistSong, Song
        playlist_songs = await PlaylistSong.filter(playlist_id=playlist_id).values_list("song_id", flat=True)
        return await Song.filter(id__in=playlist_songs).all()

    def analyze_with_pandas(self, songs: List) -> Dict:
        """Use pandas for more detailed statistical analysis.

        Args:
            songs: List of Song objects.

        Returns:
            Detailed analysis dictionary.
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is not installed")

        data = {
            "genre": [s.genre for s in songs],
            "tempo": [s.tempo for s in songs if s.tempo],
            "energy": [s.energy for s in songs if s.energy],
            "key": [s.key for s in songs if s.key],
            "duration": [s.duration for s in songs if s.duration]
        }

        df = pd.DataFrame(data)

        return {
            "genre_counts": df["genre"].value_counts().to_dict(),
            "tempo_stats": {
                "mean": df["tempo"].mean(),
                "median": df["tempo"].median(),
                "std": df["tempo"].std(),
                "min": df["tempo"].min(),
                "max": df["tempo"].max()
            },
            "energy_stats": {
                "mean": df["energy"].mean(),
                "median": df["energy"].median(),
                "std": df["energy"].std()
            },
            "key_distribution": df["key"].value_counts().to_dict(),
            "avg_duration_seconds": df["duration"].mean()
        }

    def compare_playlists(self, playlist_ids: List[str]) -> Dict:
        """Compare multiple playlists side by side.

        Args:
            playlist_ids: List of playlist IDs to compare.

        Returns:
            Comparison dictionary with analysis for each playlist.
        """
        comparisons = {}
        for pid in playlist_ids:
            comparisons[pid] = self.analyze_playlist(pid)
        return comparisons

    async def get_playlist_health_score(self, playlist_id: str) -> Dict:
        """Calculate a health/diversity score for a playlist.

        A higher score indicates a more diverse and well-balanced playlist.

        Args:
            playlist_id: The playlist to score.

        Returns:
            Dictionary with health score and breakdown.
        """
        analysis = await self.analyze_playlist(playlist_id)

        if "error" in analysis:
            return analysis

        scores = {}

        # Genre diversity score (0-100)
        num_genres = len(analysis["genre_mix"])
        scores["genre_diversity"] = min(100, num_genres * 15)

        # Tempo range score
        tempo_range = analysis["tempo_range"][1] - analysis["tempo_range"][0]
        scores["tempo_variety"] = min(100, tempo_range)

        # Artist diversity score
        scores["artist_diversity"] = analysis["artist_diversity"] * 100

        # Overall health score
        overall = sum(scores.values()) / len(scores)

        return {
            "playlist_id": playlist_id,
            "overall_health_score": round(overall, 2),
            "breakdown": scores,
            "recommendations": self._generate_recommendations(analysis, scores)
        }

    def _generate_recommendations(self, analysis: Dict, scores: Dict) -> List[str]:
        """Generate improvement recommendations based on analysis."""
        recommendations = []

        if scores.get("genre_diversity", 0) < 40:
            recommendations.append("Consider adding songs from more genres for variety.")

        if scores.get("tempo_variety", 0) < 30:
            recommendations.append("Tempo range is narrow. Add songs with different BPMs.")

        if scores.get("artist_diversity", 0) < 30:
            recommendations.append("Playlist has low artist diversity. Add more unique artists.")

        if not recommendations:
            recommendations.append("Playlist looks well-balanced. Great job!")

        return recommendations


# Module-level convenience function
async def analyze_playlist_composition(playlist_id: str) -> Dict:
    """Quick function to analyze a playlist.

    Usage:
        result = await analyze_playlist_composition(playlist_id)
    """
    analyzer = PlaylistCompositionAnalyzer()
    return await analyzer.analyze_playlist(playlist_id)

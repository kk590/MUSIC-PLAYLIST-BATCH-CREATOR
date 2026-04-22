# metrics_aggregator.py
class PlaylistMetricsAggregator:
    def daily_aggregation(self, playlist_id: str, date: date):
        plays = PlayEvent.objects.filter(playlist=playlist_id, date=date).count()
        saves = SaveEvent.objects.filter(playlist=playlist_id, date=date).count()
        PlaylistMetric.objects.update_or_create(
            playlist_id=playlist_id, date=date,
            defaults={'plays': plays, 'saves': saves}
        )

# api.py
@router.get("/playlists/{playlist_id}/performance")
def get_performance(playlist_id: str, days: int = 30):
    metrics = PlaylistMetric.objects.filter(playlist_id=playlist_id).order_by('-date')[:days]
    return serialize_time_series(metrics)

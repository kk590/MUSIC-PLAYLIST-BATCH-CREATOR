# analytics_queries.py
class UsageAnalyticsService:
    def get_dashboard_stats(self, start_date: date, end_date: date):
        return {
            "active_users": UserSession.objects.filter(date__range=(start_date, end_date)).distinct('user').count(),
            "new_playlists": Playlist.objects.filter(created__range=(start_date, end_date)).count(),
            "subscription_breakdown": Subscription.objects.values('tier').annotate(count=Count('id')),
        }

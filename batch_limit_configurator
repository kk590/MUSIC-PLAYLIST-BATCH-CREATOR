# models.py
class SubscriptionTierConfig(BaseModel):
    tier: str  # 'free', 'premium', 'enterprise'
    max_concurrent_batch_jobs: int = 2
    max_songs_per_batch: int = 100

# batch_job_validator.py
def validate_batch_job(user_id: str, song_count: int):
    user = get_user(user_id)
    config = get_tier_config(user.subscription_tier)
    if song_count > config.max_songs_per_batch:
        raise LimitExceededError(f"Maximum {config.max_songs_per_batch} songs allowed.")
    if get_active_job_count(user_id) >= config.max_concurrent_batch_jobs:
        raise LimitExceededError("Too many active jobs.")

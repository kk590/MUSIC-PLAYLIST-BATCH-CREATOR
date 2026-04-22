# preference_collector.py
class PreferenceCollector:
    def record_interaction(self, user_id: str, song_id: str, action: str, timestamp: datetime):
        # Store in database table 'user_interactions'
        pass

# model_trainer.py
class ModelTrainer:
    def train_for_user(self, user_id: str):
        interactions = fetch_interactions(user_id)
        if len(interactions) < MIN_SAMPLES:
            return None
        # Feature engineering: song metadata, user history embeddings
        X, y = prepare_training_data(interactions)
        model = train_collaborative_filtering(X, y)
        save_model(user_id, model)
        return model

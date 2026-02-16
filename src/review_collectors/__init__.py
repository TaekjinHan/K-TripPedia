"""Review collectors for mobile app stores."""

from src.review_collectors.apple_store import collect_apple_reviews
from src.review_collectors.google_play import collect_google_reviews

__all__ = ["collect_apple_reviews", "collect_google_reviews"]

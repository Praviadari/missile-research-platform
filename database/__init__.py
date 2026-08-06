"""Database package — SQLAlchemy models and session helpers."""

from database.models import AnalyticsEvent, Base, ResearchNote, SavedSearch, User, UserTier
from database.session import (
    get_user_tier,
    tier_counts,
    update_tier_by_stripe_customer,
    upsert_user,
)

__all__ = [
    "AnalyticsEvent",
    "Base",
    "ResearchNote",
    "SavedSearch",
    "User",
    "UserTier",
    "get_user_tier",
    "tier_counts",
    "update_tier_by_stripe_customer",
    "upsert_user",
]

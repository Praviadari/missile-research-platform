"""
analytics/tracker.py
=====================
Privacy-preserving product analytics for the Missile Research Platform.

Uses PostHog (self-hosted or cloud) for event tracking. Falls back to a
no-op logger when POSTHOG_API_KEY is not set.

No personally identifiable information is stored in events — user IDs are
anonymised Supabase UUIDs. No IP addresses are sent.

USAGE
-----
    from analytics.tracker import track
    track("page_view", {"page": "missile_database", "missiles_shown": 12})
    track("filter_applied", {"category": "SRBM", "country": "Iran"})
"""

import os
import logging
import streamlit as st

logger = logging.getLogger(__name__)

_POSTHOG_KEY = os.getenv("POSTHOG_API_KEY", "")
_ph = None


def _client():
    """Lazy-initialise PostHog client."""
    global _ph
    if _ph is not None:
        return _ph
    if not _POSTHOG_KEY:
        return None
    try:
        from posthog import Posthog
        _ph = Posthog(
            _POSTHOG_KEY,
            host=os.getenv("POSTHOG_HOST", "https://app.posthog.com"),
        )
        return _ph
    except ImportError:
        logger.debug("posthog not installed — analytics disabled")
        return None


def _distinct_id() -> str:
    """Return anonymised user ID for analytics."""
    uid = st.session_state.get("auth.user_id")
    if uid:
        return f"user:{uid[:12]}"   # truncated — never full UUID
    sid = st.session_state.get("_session_id", "anon")
    return f"anon:{sid[:8]}"


def track(event: str, properties: dict | None = None) -> None:
    """
    Track a product analytics event.

    Parameters
    ----------
    event      : str   Event name, e.g. "page_view", "filter_applied"
    properties : dict  Additional properties. Never include PII.
    """
    ph = _client()
    if ph is None:
        logger.debug("analytics.track [no-op]: %s %s", event, properties or {})
        return

    props = properties or {}
    props.setdefault("tier",    st.session_state.get("auth.tier", "anon"))
    props.setdefault("page",    st.session_state.get("page", "unknown"))
    props.setdefault("platform", "missile_platform_v2")

    try:
        ph.capture(distinct_id=_distinct_id(), event=event, properties=props)
    except Exception as e:
        logger.warning("analytics.track error: %s", e)


def page_view(page: str, extra: dict | None = None) -> None:
    """Shorthand for page view events."""
    props = {"page": page}
    if extra:
        props.update(extra)
    track("page_view", props)


def identify(tier: str, extra: dict | None = None) -> None:
    """
    Identify the current user session with their tier.
    Call after successful sign-in or tier change.
    """
    ph = _client()
    if ph is None:
        return
    props = {"tier": tier}
    if extra:
        props.update(extra)
    try:
        ph.identify(distinct_id=_distinct_id(), properties=props)
    except Exception as e:
        logger.warning("analytics.identify error: %s", e)

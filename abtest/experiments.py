"""
abtest/experiments.py
======================
Lightweight A/B testing framework for the Missile Research Platform.

Assigns users to experiment variants deterministically (hashed user ID),
tracks exposures and conversions, and integrates with PostHog feature flags
when available.

USAGE
-----
    from abtest.experiments import get_variant, track_conversion

    # Get the variant for the current user on a given experiment
    variant = get_variant("home_cta_style")   # → "control" | "treatment_a"

    # Track a conversion event
    track_conversion("home_cta_style", "upgrade_clicked")
"""

import hashlib
import os
import logging
import streamlit as st

logger = logging.getLogger(__name__)

# ── Experiment registry ────────────────────────────────────────────────────────
# Each experiment defines:
#   variants : list of variant names (first = control)
#   traffic  : fraction of users exposed (0.0–1.0)
#   active   : bool — set False to stop the experiment

EXPERIMENTS: dict[str, dict] = {
    "home_cta_style": {
        "variants": ["control", "red_gradient"],
        "traffic":  1.0,
        "active":   True,
        "description": "Test two hero CTA button styles on the home page",
    },
    "sidebar_order": {
        "variants": ["control", "learn_first"],
        "traffic":  0.5,
        "active":   True,
        "description": "Test reordering sidebar to put Learn section first",
    },
    "onboarding_flow": {
        "variants": ["control", "video_first", "db_first"],
        "traffic":  1.0,
        "active":   False,
        "description": "Test onboarding page sequencing",
    },
}


def _user_hash(user_key: str, experiment: str) -> float:
    """Return a stable float 0–1 for (user, experiment) pair."""
    raw = f"{user_key}:{experiment}"
    digest = hashlib.md5(raw.encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _user_key() -> str:
    uid = st.session_state.get("auth.user_id")
    if uid:
        return uid
    # For anon users, create a session-stable key
    if "abtest_session_key" not in st.session_state:
        import uuid
        st.session_state["abtest_session_key"] = str(uuid.uuid4())
    return st.session_state["abtest_session_key"]


def get_variant(experiment: str) -> str:
    """
    Return the variant name for the current user on the given experiment.

    Returns "control" if:
      - Experiment is not in registry
      - Experiment is not active
      - User falls outside traffic bucket
    """
    exp = EXPERIMENTS.get(experiment)
    if not exp or not exp.get("active"):
        return "control"

    key  = _user_key()
    h    = _user_hash(key, experiment)

    # Check if user is in the traffic bucket
    if h > exp["traffic"]:
        return "control"

    variants = exp["variants"]
    if not variants:
        return "control"

    # Assign to variant proportionally
    idx = int(h / exp["traffic"] * len(variants))
    idx = min(idx, len(variants) - 1)
    variant = variants[idx]

    # Track exposure (once per session per experiment)
    exposure_key = f"abtest_exposed_{experiment}"
    if not st.session_state.get(exposure_key):
        st.session_state[exposure_key] = True
        _track_exposure(experiment, variant)

    return variant


def track_conversion(experiment: str, event: str) -> None:
    """
    Track a conversion event for an A/B experiment.

    experiment : str  The experiment name
    event      : str  Conversion event name, e.g. "upgrade_clicked"
    """
    variant = get_variant(experiment)
    _track_event(f"abtest_conversion", {
        "experiment": experiment,
        "variant":    variant,
        "event":      event,
    })


def _track_exposure(experiment: str, variant: str) -> None:
    _track_event("abtest_exposure", {
        "experiment": experiment,
        "variant":    variant,
    })


def _track_event(event: str, props: dict) -> None:
    try:
        from analytics.tracker import track
        track(event, props)
    except Exception as e:
        logger.debug("abtest track failed: %s", e)


def list_active_experiments() -> list[dict]:
    """Return list of all active experiments with current user's variants."""
    return [
        {
            "name":        name,
            "description": exp.get("description", ""),
            "variant":     get_variant(name),
            "variants":    exp["variants"],
        }
        for name, exp in EXPERIMENTS.items()
        if exp.get("active")
    ]

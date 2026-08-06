"""
feedback/feedback_widget.py
============================
In-app user feedback collection for the Missile Research Platform.

Renders a lightweight feedback panel that:
  - Captures thumbs-up / thumbs-down reactions per page
  - Optional free-text comment (max 500 chars)
  - Stores to Supabase `feedback` table (or logs if not configured)
  - Can prompt for feature requests

USAGE
-----
    from feedback.feedback_widget import render_feedback_bar
    render_feedback_bar()   # call at the bottom of any page
"""

import os
import logging
import streamlit as st

logger = logging.getLogger(__name__)

SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def _submit_feedback(page: str, rating: str, comment: str) -> bool:
    """
    Store feedback. Returns True on success.
    Falls back to logger when Supabase is not configured.
    """
    user_id = st.session_state.get("auth.user_id", "anon")
    tier    = st.session_state.get("auth.tier", "anon")

    record = {
        "page":    page,
        "rating":  rating,
        "comment": comment[:500],
        "user_id": user_id,
        "tier":    tier,
    }

    if not SUPABASE_URL:
        logger.info("Feedback [dev]: %s", record)
        return True

    try:
        import requests
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/feedback",
            headers={
                "apikey":        SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {st.session_state.get('auth.access_token', SUPABASE_ANON_KEY)}",
                "Content-Type":  "application/json",
                "Prefer":        "return=minimal",
            },
            json=record,
            timeout=5,
        )
        return r.ok
    except Exception as e:
        logger.warning("Feedback submission failed: %s", e)
        return False


def render_feedback_bar(page: str | None = None) -> None:
    """
    Render a compact feedback bar at the bottom of the current page.

    Parameters
    ----------
    page : str | None
        Page identifier for the feedback record. Defaults to
        st.session_state["page"].
    """
    page = page or st.session_state.get("page", "unknown")
    key  = f"fb_{page}"

    # Don't render if already submitted this session
    if st.session_state.get(f"{key}_submitted"):
        st.markdown(
            "<div style='text-align:center; color:#27AE60; font-size:0.85rem; padding:8px;'>"
            "✅ Thanks for your feedback!"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        "<div style='border-top:1px solid #1E2235; margin-top:24px; padding-top:12px; "
        "text-align:center; color:#6B6F84; font-size:0.85rem;'>"
        "Was this page useful?"
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("👍", key=f"{key}_up", use_container_width=True):
                st.session_state[f"{key}_rating"] = "positive"
        with c2:
            if st.button("👎", key=f"{key}_down", use_container_width=True):
                st.session_state[f"{key}_rating"] = "negative"

    rating = st.session_state.get(f"{key}_rating")
    if rating:
        with col3:
            comment = st.text_input(
                "Optional: tell us more",
                key=f"{key}_comment",
                placeholder="What could be improved?",
                max_chars=500,
            )
        col_a, col_b, col_c = st.columns([2, 1, 2])
        with col_b:
            if st.button("Submit", key=f"{key}_submit", use_container_width=True):
                ok = _submit_feedback(page, rating, comment)
                st.session_state[f"{key}_submitted"] = True
                st.rerun()

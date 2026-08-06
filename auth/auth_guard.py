"""auth/auth_guard.py — Feature-gate helper and decorator."""

from __future__ import annotations

import functools

import streamlit as st

from auth.auth import can_access, current_tier

TIER_FEATURES = {
    "pro": [
        ("📈 Trajectory Simulator", "Physics-based 2D trajectory with atmosphere and drag"),
        ("🔥 Propulsion Analysis", "Isp curves, staging optimisation, mass fraction explorer"),
        ("⚡ Hypersonic Lab", "HGV, scramjet, thermal management deep-dive"),
        ("🛡️ Defense Systems Lab", "Layered defense engagement envelope reference"),
        ("🛠️ Design Lab", "7-step guided missile design research workflow"),
        ("🌐 3D Visualizer", "Three-dimensional trajectory and engagement visualizer"),
    ],
}


def gate_page(
    required_tier: str,
    page_key: str,
    page_title: str | None = None,
) -> bool:
    """
    Return True if the user may open page_key.
    Otherwise render the upgrade wall and return False.

    page_key must match auth.PRO_PAGES / ENTERPRISE_PAGES keys (e.g. "trajectory").
    """
    title = page_title or page_key.replace("_", " ").title()
    if can_access(page_key):
        return True

    tier = current_tier()
    tier_order = {"anon": 0, "free": 1, "pro": 2, "enterprise": 3}
    req_order = {"free": 1, "pro": 2, "enterprise": 3}
    if tier_order.get(tier, 0) >= req_order.get(required_tier, 2):
        return True

    st.markdown(
        f"""<div class='mp-gate'>
        <div class='mp-gate-icon'>🔒</div>
        <div class='mp-gate-title'>{title}</div>
        <div class='mp-gate-body'>This feature requires a <strong>Pro</strong> subscription.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    features = TIER_FEATURES.get(required_tier, [])
    if features:
        from ui.theme import feature_row

        st.markdown("**Pro includes:**")
        for feat_title, desc in features:
            st.markdown(feature_row(feat_title, desc), unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⚡ Upgrade to Pro", type="primary", use_container_width=True):
            st.session_state["auth.show_auth_modal"] = True
            st.session_state["auth.auth_mode"] = "upgrade"
            st.rerun()
    return False


def require_tier(tier: str, page_key: str | None = None):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = page_key or fn.__name__
            if not gate_page(tier, key, fn.__name__.replace("_", " ").title()):
                return
            return fn(*args, **kwargs)

        return wrapper

    return decorator

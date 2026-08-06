"""
auth/auth.py
=============
Authentication layer — Supabase Auth integration.
Set SUPABASE_URL and SUPABASE_ANON_KEY in .env to activate.

Session-state keys written here:
  auth.user_id, auth.email, auth.tier, auth.display_name,
  auth.access_token, auth.is_authenticated, auth.stripe_customer_id
"""

from __future__ import annotations

import logging
import os
import time

import streamlit as st

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")

ADMIN_USER_IDS = {
    x.strip() for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()
}
ENTERPRISE_USER_IDS = {
    x.strip() for x in os.getenv("ENTERPRISE_USER_IDS", "").split(",") if x.strip()
} | ADMIN_USER_IDS

PUBLIC_PAGES = {
    "home",
    "missile_database",
    "historical_timeline",
    "treaty_guide",
    "resource_library",
    "learning_center",
}

PRO_PAGES = {
    "trajectory",
    "propulsion",
    "reentry",
    "hypersonic",
    "defense_lab",
    "visualizer",
    "design_lab",
}

ENTERPRISE_PAGES = {"admin", "admin_ops"}

TIER_LABELS = {
    "anon": ("🔓 Free", "#6B6F84"),
    "free": ("🔓 Free", "#6B6F84"),
    "pro": ("⚡ Pro", "#E74C3C"),
    "enterprise": ("🏢 Enterprise", "#FFD700"),
}


def setup():
    """Called once per app load. Verifies Supabase token if present."""
    if not SUPABASE_URL:
        return
    token = st.session_state.get("auth.access_token")
    if token and _token_valid():
        _resolve_tier()
    elif token:
        _refresh_token()


def _token_valid() -> bool:
    expiry = st.session_state.get("auth.token_expiry", 0)
    return time.time() < expiry - 60


def _refresh_token():
    try:
        import requests

        refresh = st.session_state.get("auth.refresh_token")
        if not refresh:
            _clear_session()
            return
        r = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            json={"refresh_token": refresh},
            timeout=8,
        )
        if r.ok:
            _set_session(r.json())
        else:
            _clear_session()
    except Exception as e:
        logger.warning("Token refresh failed: %s", e)


def _resolve_tier():
    uid = st.session_state.get("auth.user_id", "")
    if uid in ENTERPRISE_USER_IDS:
        st.session_state["auth.tier"] = "enterprise"
        return

    db_tier = None
    try:
        from database.session import get_user_tier

        db_tier = get_user_tier(uid) if uid else None
    except Exception:
        db_tier = None

    # Stripe is source of truth when configured; DB is durable fallback.
    if STRIPE_SECRET_KEY:
        try:
            from billing.stripe_billing import get_tier_from_stripe

            st.session_state["auth.tier"] = get_tier_from_stripe(
                st.session_state.get("auth.stripe_customer_id")
            )
            return
        except Exception:
            st.session_state["auth.tier"] = db_tier or "free"
            return

    st.session_state["auth.tier"] = db_tier or "free"


def sign_in(email: str, password: str) -> tuple[bool, str]:
    try:
        import requests

        r = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
            timeout=10,
        )
        if r.ok:
            _set_session(r.json())
            return True, ""
        return False, r.json().get("error_description", "Sign-in failed.")
    except Exception as e:
        return False, str(e)


def sign_up(email: str, password: str) -> tuple[bool, str]:
    try:
        import requests

        r = requests.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
            timeout=10,
        )
        if r.ok:
            return True, ""
        return False, r.json().get("msg", "Sign-up failed.")
    except Exception as e:
        return False, str(e)


def sign_out():
    _clear_session()


def is_authenticated() -> bool:
    return bool(st.session_state.get("auth.is_authenticated"))


def current_tier() -> str:
    return st.session_state.get("auth.tier", "anon") or "anon"


def can_access(page_key: str) -> bool:
    """Return True only for known pages the current tier may open. Default deny."""
    tier = current_tier()
    if page_key in PUBLIC_PAGES:
        return True
    if page_key in ENTERPRISE_PAGES:
        return tier == "enterprise"
    if page_key in PRO_PAGES:
        return tier in ("pro", "enterprise")
    return False


def _ensure_stripe_customer(user_id: str, email: str, meta: dict) -> str | None:
    cid = meta.get("stripe_customer_id") or st.session_state.get("auth.stripe_customer_id")
    if cid:
        return cid
    if not STRIPE_SECRET_KEY or not email:
        return None
    try:
        from billing.stripe_billing import create_customer

        return create_customer(email, user_id)
    except Exception as e:
        logger.warning("Stripe customer ensure failed: %s", e)
        return None


def _set_session(data: dict):
    user = data.get("user", {})
    meta = user.get("user_metadata", {}) or {}
    email = user.get("email", "") or ""
    uid = user.get("id", "") or ""
    display = meta.get("full_name") or (email.split("@")[0] if email else "User")
    stripe_cid = _ensure_stripe_customer(uid, email, meta)
    st.session_state.update(
        {
            "auth.user_id": uid,
            "auth.email": email,
            "auth.display_name": display,
            "auth.access_token": data.get("access_token"),
            "auth.refresh_token": data.get("refresh_token"),
            "auth.token_expiry": time.time() + data.get("expires_in", 3600),
            "auth.is_authenticated": True,
            "auth.stripe_customer_id": stripe_cid,
        }
    )
    _resolve_tier()
    try:
        from database.session import upsert_user

        upsert_user(
            uid,
            email,
            display_name=display,
            tier=st.session_state.get("auth.tier", "free"),
            stripe_customer_id=stripe_cid,
        )
    except Exception as e:
        logger.warning("user upsert skipped: %s", e)


def _clear_session():
    for k in [
        "auth.user_id",
        "auth.email",
        "auth.display_name",
        "auth.access_token",
        "auth.refresh_token",
        "auth.token_expiry",
        "auth.is_authenticated",
        "auth.stripe_customer_id",
    ]:
        st.session_state[k] = None
    st.session_state["auth.tier"] = "anon"
    st.session_state["auth.is_authenticated"] = False

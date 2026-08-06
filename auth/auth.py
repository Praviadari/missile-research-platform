"""
auth/auth.py
=============
Authentication layer — Supabase Auth integration.
Identical in structure to drone_platform_v3/auth/auth.py.
Set SUPABASE_URL and SUPABASE_ANON_KEY in .env to activate.

Session-state keys written here:
  auth.user_id, auth.email, auth.tier, auth.display_name,
  auth.access_token, auth.is_authenticated
"""

import os, logging, time
import streamlit as st

logger = logging.getLogger(__name__)

SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
ENTERPRISE_USER_IDS = set(os.getenv("ENTERPRISE_USER_IDS", "").split(","))

PUBLIC_PAGES = {"home", "missile_database", "historical_timeline", "treaty_guide",
                "resource_library", "learning_center"}

PRO_PAGES = {"trajectory", "propulsion", "reentry", "hypersonic", "defense_lab",
             "saturation", "visualizer", "design_lab", "bom_manager",
             "manufacturing", "supply_chain"}

ENTERPRISE_PAGES = {"admin", "admin_ops"}

TIER_LABELS = {
    "anon":       ("🔓 Free",       "#6B6F84"),
    "free":       ("🔓 Free",       "#6B6F84"),
    "pro":        ("⚡ Pro",         "#E74C3C"),
    "enterprise": ("🏢 Enterprise", "#FFD700"),
}


def setup():
    """Called once per app load. Verifies Supabase token if present."""
    if not SUPABASE_URL:
        return  # dev mode — session already initialised in app.py
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
            data = r.json()
            _set_session(data)
        else:
            _clear_session()
    except Exception as e:
        logger.warning("Token refresh failed: %s", e)


def _resolve_tier():
    uid = st.session_state.get("auth.user_id", "")
    if uid in ENTERPRISE_USER_IDS:
        st.session_state["auth.tier"] = "enterprise"
        return
    if STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            subs = stripe.Subscription.list(customer=st.session_state.get("auth.stripe_customer_id",""), status="active", limit=1)
            st.session_state["auth.tier"] = "pro" if subs.data else "free"
        except Exception:
            st.session_state["auth.tier"] = "free"
    else:
        st.session_state["auth.tier"] = "free"


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
    tier = current_tier()
    if page_key in PUBLIC_PAGES:      return True
    if page_key in ENTERPRISE_PAGES:  return tier == "enterprise"
    if page_key in PRO_PAGES:         return tier in ("pro", "enterprise")
    return True


def _set_session(data: dict):
    user = data.get("user", {})
    meta = user.get("user_metadata", {})
    st.session_state.update({
        "auth.user_id":          user.get("id"),
        "auth.email":            user.get("email"),
        "auth.display_name":     meta.get("full_name") or user.get("email","").split("@")[0],
        "auth.access_token":     data.get("access_token"),
        "auth.refresh_token":    data.get("refresh_token"),
        "auth.token_expiry":     time.time() + data.get("expires_in", 3600),
        "auth.is_authenticated": True,
    })
    _resolve_tier()


def _clear_session():
    for k in ["auth.user_id","auth.email","auth.display_name","auth.access_token",
              "auth.refresh_token","auth.token_expiry","auth.is_authenticated"]:
        st.session_state[k] = None
    st.session_state["auth.tier"] = "anon"
    st.session_state["auth.is_authenticated"] = False

"""auth/auth_modal.py — In-app authentication modal."""
import streamlit as st
from auth.auth import sign_in, sign_up, sign_out, is_authenticated, current_tier, TIER_LABELS

STRIPE_PAYMENT_LINK = os.getenv("STRIPE_PAYMENT_LINK", "#") if False else "#"
PRO_PRICE = "$29/mo"

import os
STRIPE_PAYMENT_LINK = os.getenv("STRIPE_PAYMENT_LINK", "#")

def render_auth_modal():
    if not st.session_state.get("auth.show_auth_modal", False):
        return
    mode = st.session_state.get("auth.auth_mode", "login")
    try:
        _render_as_dialog(mode)
    except Exception:
        _render_as_sidebar(mode)

@st.dialog("🚀 Missile Research Platform", width="small")
def _render_as_dialog(mode):
    _render_auth_content(mode)

def _render_as_sidebar(mode):
    with st.sidebar.expander("🔐 Sign In / Sign Up", expanded=True):
        _render_auth_content(mode)

def _render_auth_content(mode):
    if mode == "upgrade":
        st.markdown("### ⚡ Upgrade to Pro")
        st.markdown(f"**{PRO_PRICE}** — unlocks all analysis tools")
        st.link_button("Upgrade Now", STRIPE_PAYMENT_LINK, use_container_width=True)
        if st.button("Cancel"): st.session_state["auth.show_auth_modal"] = False; st.rerun()
        return

    if is_authenticated():
        st.success(f"Signed in as {st.session_state.get('auth.email','')}")
        if st.button("Sign Out"):
            sign_out(); st.session_state["auth.show_auth_modal"] = False; st.rerun()
        return

    tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
    with tab_login:
        email = st.text_input("Email", key="login_email")
        pw    = st.text_input("Password", type="password", key="login_pw")
        if st.button("Sign In", type="primary", use_container_width=True):
            ok, err = sign_in(email, pw)
            if ok: st.session_state["auth.show_auth_modal"] = False; st.rerun()
            else:  st.error(err)
    with tab_signup:
        email2 = st.text_input("Email", key="signup_email")
        pw2    = st.text_input("Password", type="password", key="signup_pw")
        if st.button("Create Account", type="primary", use_container_width=True):
            ok, err = sign_up(email2, pw2)
            if ok: st.success("Account created! Check your email to verify.")
            else:  st.error(err)

def render_user_menu():
    if is_authenticated():
        tier   = current_tier()
        label, color = TIER_LABELS.get(tier, ("👤 Guest","#6B6F84"))
        name   = st.session_state.get("auth.display_name","")
        st.sidebar.markdown(
            f"<div style='text-align:center; padding:4px 0 6px;'>"
            f"<span style='background:{color}22; color:{color}; padding:2px 10px; border-radius:20px; font-size:0.72rem; font-weight:700;'>{label}</span><br>"
            f"<span style='color:#6B6F84; font-size:0.78rem;'>{name}</span>"
            f"</div>", unsafe_allow_html=True,
        )
        col1, col2 = st.sidebar.columns(2)
        if col2.button("Sign Out", use_container_width=True):
            sign_out(); st.rerun()
    else:
        if st.sidebar.button("🔐 Sign In / Sign Up", use_container_width=True):
            st.session_state["auth.show_auth_modal"] = True
            st.session_state["auth.auth_mode"] = "login"
            st.rerun()

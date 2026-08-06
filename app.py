"""
app.py — Missile Analysis & Research Platform v2
=================================================
Entry point. Run with:  streamlit run app.py

Architecture (three-layer separation)
--------------------------------------
  data/          JSON data files — missiles, treaties, events, resources
  modules/       Streamlit page renderers — each exports render()
  ui/            Reusable Streamlit components (sidebar, charts, theme)

Pro-gated pages (trajectory, design lab, etc.) are noted in sidebar.py
and auth/auth.py — they require a Pro tier subscription.

Public pages (database browser, treaty guide, historical timeline,
learning center, resource library) are free and require no login.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Missile Research Platform v2",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.theme import inject_global_css
inject_global_css()


# ── Session-state initialisation ──────────────────────────────────────────────
def _init_session():
    dev_mode = not bool(os.getenv("SUPABASE_URL"))
    defaults = {
        "page":                  "home",
        "auth.user_id":          "dev-user-001" if dev_mode else None,
        "auth.email":            "dev@local"    if dev_mode else None,
        "auth.tier":             "pro"          if dev_mode else "anon",
        "auth.display_name":     "Dev User"     if dev_mode else "Guest",
        "auth.access_token":     "dev-token"    if dev_mode else None,
        "auth.refresh_token":    None,
        "auth.is_authenticated": dev_mode,
        "auth.token_expiry":     0,
        "auth.show_auth_modal":  False,
        "auth.auth_mode":        "login",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def gate_page(required_tier: str, page_name: str) -> bool:
    """Return True if user can access; otherwise render upgrade wall and return False."""
    try:
        from auth.auth_guard import gate_page as _gate
        return _gate(required_tier, page_name)
    except ImportError:
        tier = st.session_state.get("auth.tier", "anon")
        tier_order = {"anon": 0, "free": 1, "pro": 2, "enterprise": 3}
        required_order = {"free": 1, "pro": 2, "enterprise": 3}
        if tier_order.get(tier, 0) >= required_order.get(required_tier, 2):
            return True
        st.markdown(
            f"""
            <div class='mp-gate'>
                <div class='mp-gate-icon'>🔒</div>
                <div class='mp-gate-title'>{page_name} — Pro Feature</div>
                <div class='mp-gate-body'>
                    This analysis tool requires a Pro subscription.<br>
                    Upgrade to unlock trajectory simulation, design lab,
                    and advanced analysis modules.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚡ Upgrade to Pro", type="primary", use_container_width=True):
                st.session_state["auth.show_auth_modal"] = True
                st.session_state["auth.auth_mode"] = "upgrade"
                st.rerun()
        return False


# ── Page router ───────────────────────────────────────────────────────────────
def main():
    _init_session()

    # Run auth setup if Supabase is configured
    try:
        from auth.auth import setup as auth_setup
        auth_setup()
    except ImportError:
        pass

    # Render auth modal if requested
    try:
        from auth.auth_modal import render_auth_modal
        render_auth_modal()
    except ImportError:
        pass

    from ui.sidebar import render as render_sidebar
    render_sidebar(default_page="home")

    page = st.session_state.get("page", "home")

    # ── Public pages ─────────────────────────────────────────────────────────
    if page == "home":
        from modules.onboarding import render
        render()

    elif page == "missile_database":
        from modules.missile_database import render
        render()

    elif page == "historical_timeline":
        from modules.historical_timeline import render
        render()

    elif page == "treaty_guide":
        from modules.treaty_guide import render
        render()

    elif page == "resource_library":
        from modules.resource_library import render
        render()

    elif page == "learning_center":
        from modules.learning_center import render
        render()

    # ── Pro pages (gated) ─────────────────────────────────────────────────────
    elif page == "trajectory":
        if gate_page("pro", "Trajectory Simulator"):
            from modules.trajectory_simulator import render
            render()

    elif page == "propulsion":
        if gate_page("pro", "Propulsion Analysis"):
            from modules.propulsion_analysis import render
            render()

    elif page == "reentry":
        if gate_page("pro", "Reentry Analysis"):
            from modules.reentry_analysis import render
            render()

    elif page == "hypersonic":
        if gate_page("pro", "Hypersonic Lab"):
            from modules.hypersonic_lab import render
            render()

    elif page == "defense_lab":
        if gate_page("pro", "Defense Systems Lab"):
            from modules.defense_lab import render
            render()

    elif page == "saturation":
        if gate_page("pro", "Saturation Modeler"):
            from modules.saturation_lab import render
            render()

    elif page == "visualizer":
        if gate_page("pro", "3D Trajectory Visualizer"):
            from modules.trajectory_visualizer import render
            render()

    elif page == "design_lab":
        if gate_page("pro", "Missile Design Lab"):
            from modules.design_lab import render
            render()

    elif page == "bom_manager":
        if gate_page("pro", "BOM Manager"):
            from modules.bom_manager import render
            render()

    elif page == "manufacturing":
        if gate_page("pro", "Manufacturing Hub"):
            from modules.manufacturing_hub import render
            render()

    elif page == "supply_chain":
        if gate_page("pro", "Supply Chain"):
            from modules.supply_chain import render
            render()

    # ── Admin pages ───────────────────────────────────────────────────────────
    elif page == "admin":
        if gate_page("enterprise", "Admin Dashboard"):
            from admin.admin_dashboard import render
            render()

    elif page == "admin_ops":
        if gate_page("enterprise", "GrowthOps"):
            from admin.admin_ops import render
            render()

    else:
        st.error(f"Page '{page}' not found.")
        if st.button("← Go Home"):
            st.session_state["page"] = "home"
            st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#6B6F84; font-size:0.78rem;'>"
        "Missile Analysis & Research Platform v2 · Open-source defense research · "
        "All data sourced from public, declassified, and academic references"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__" or True:
    main()

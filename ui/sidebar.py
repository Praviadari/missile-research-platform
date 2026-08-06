"""
ui/sidebar.py
=============
Reusable sidebar component for the Missile Analysis & Research Platform.

Navigation is grouped into four areas:
  - 📚 Research: public-access pages (database browser, treaties, history)
  - 🔬 Analysis: pro-gated analysis tools
  - 📖 Learn: education and resources
  - ⚙️  Admin: admin-only dashboard links
"""

import os
import streamlit as st

# ── Page catalogue ────────────────────────────────────────────────────────────
PAGE_GROUPS = {
    "📚 Research": [
        ("🏠 Home",                      "home"),
        ("📋 Missile Database",          "missile_database"),
        ("📅 Historical Timeline",       "historical_timeline"),
        ("📜 Treaty & Policy Guide",     "treaty_guide"),
        ("📖 Resource Library",          "resource_library"),
    ],
    "📚 Learn": [
        ("🎓 Learning Center",           "learning_center"),
    ],
    "⚡ Pro — Analysis": [
        ("📈 Trajectory Simulator",      "trajectory"),
        ("🔥 Propulsion Analysis",       "propulsion"),
        ("🌡️ Reentry Analysis",          "reentry"),
        ("⚡ Hypersonic Lab",            "hypersonic"),
        ("🛡️ Defense Systems Lab",       "defense_lab"),
        ("🌐 3D Visualizer",             "visualizer"),
    ],
    "⚡ Pro — Design": [
        ("🛠️ Design Lab",               "design_lab"),
    ],
}

# Pages requiring at least Pro tier
PRO_PAGES = {
    "trajectory", "propulsion", "reentry", "hypersonic",
    "defense_lab", "visualizer", "design_lab",
}

ALL_PAGES: list[tuple[str, str]] = [
    (lbl, key)
    for pages in PAGE_GROUPS.values()
    for lbl, key in pages
]


def _current_tier() -> str:
    return st.session_state.get("auth.tier", "anon") or "anon"


def _is_admin() -> bool:
    """Admin nav only for configured admin/enterprise users (or DEV_UNLOCK_PRO)."""
    if os.getenv("DEV_UNLOCK_PRO", "false").lower() in ("1", "true", "yes"):
        return True
    admin_ids = {
        x.strip()
        for x in (
            os.getenv("ADMIN_USER_IDS", "") + "," + os.getenv("ENTERPRISE_USER_IDS", "")
        ).split(",")
        if x.strip()
    }
    return st.session_state.get("auth.user_id", "") in admin_ids


def _nav_button(label: str, key: str) -> None:
    tier = _current_tier()
    is_locked = key in PRO_PAGES and tier not in ("pro", "enterprise")
    display_label = f"{label}  🔒" if is_locked else label

    if st.sidebar.button(
        display_label,
        key=f"nav_{key}",
        use_container_width=True,
        type="secondary",
    ):
        st.session_state["page"] = key
        st.rerun()


def render(default_page: str = "home") -> None:
    """Render the full sidebar. Call once from app.py before the page router."""
    if "page" not in st.session_state:
        st.session_state["page"] = default_page

    # ── Logo ──────────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        """
        <div style='text-align:center; padding:12px 0 4px;'>
            <span style='font-size:2.4rem;'>🚀</span><br>
            <span style='font-size:1.1rem; font-weight:700; color:#E74C3C;'>
                Missile Research Platform
            </span><br>
            <span style='font-size:0.72rem; color:#6B6F84;'>
                v2.0 — Open-Source Defense Research
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── User auth widget ──────────────────────────────────────────────────────
    try:
        from auth.auth_modal import render_user_menu
        render_user_menu()
    except ImportError:
        tier = _current_tier()
        tier_cfg = {
            "pro":        ("⚡ Pro",         "#E74C3C"),
            "enterprise": ("🏢 Enterprise",  "#FFD700"),
            "free":       ("🔓 Free",        "#6B6F84"),
            "anon":       ("👤 Guest",       "#6B6F84"),
        }
        lbl, color = tier_cfg.get(tier, ("👤 Guest", "#6B6F84"))
        name = st.session_state.get("auth.display_name", "")
        st.sidebar.markdown(
            f"<div style='text-align:center; padding:4px 0 6px;'>"
            f"<span style='background:{color}22; color:{color}; "
            f"padding:2px 10px; border-radius:20px; font-size:0.72rem; font-weight:700;'>"
            f"{lbl}</span>"
            f"{'  <span style=\"color:#6B6F84; font-size:0.78rem;\">' + name + '</span>' if name else ''}"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.sidebar.divider()

    # ── Search ────────────────────────────────────────────────────────────────
    query = st.sidebar.text_input(
        "🔍 Search pages…", key="sidebar_search", placeholder="e.g. treaty, timeline…"
    ).strip().lower()

    if query:
        matches = [(lbl, k) for lbl, k in ALL_PAGES if query in lbl.lower()]
        if matches:
            st.sidebar.markdown(
                f"<span style='color:#6B6F84; font-size:0.78rem;'>"
                f"{len(matches)} match{'es' if len(matches) != 1 else ''}</span>",
                unsafe_allow_html=True,
            )
            for lbl, key in matches:
                _nav_button(lbl, key)
        else:
            st.sidebar.markdown(
                "<span style='color:#E74C3C; font-size:0.82rem;'>No pages found.</span>",
                unsafe_allow_html=True,
            )
        st.sidebar.divider()
        return

    # ── Grouped navigation ────────────────────────────────────────────────────
    for group_label, pages in PAGE_GROUPS.items():
        st.sidebar.markdown(
            f"<div style='color:#6B6F84; font-size:0.74rem; font-weight:600; "
            f"letter-spacing:0.08em; padding:10px 0 4px; text-transform:uppercase;'>"
            f"{group_label}</div>",
            unsafe_allow_html=True,
        )
        for lbl, key in pages:
            _nav_button(lbl, key)

    # ── Admin ─────────────────────────────────────────────────────────────────
    if _is_admin():
        st.sidebar.markdown(
            "<div style='color:#6B6F84; font-size:0.74rem; font-weight:600; "
            "letter-spacing:0.08em; padding:6px 0 4px; text-transform:uppercase;'>"
            "🔧 Admin</div>",
            unsafe_allow_html=True,
        )
        _nav_button("🛠️ Admin Dashboard", "admin")
        _nav_button("⚙️ GrowthOps", "admin_ops")
        st.sidebar.divider()

    # ── Quick reference ───────────────────────────────────────────────────────
    with st.sidebar.expander("📐 Quick Reference", expanded=False):
        st.markdown(
            """
            **ISA Atmosphere (Sea Level)**
            | Quantity | Value |
            |---|---|
            | Air density ρ | 1.225 kg/m³ |
            | Temperature | 15 °C / 288.15 K |
            | Speed of sound | 340.3 m/s |
            | Pressure | 101.325 kPa |

            **Rocket Equation**  Δv = Isp × g₀ × ln(m₀/m_f)

            **MTCR Thresholds**
            - Payload > 500 kg AND range > 300 km → Category I control
            - Category I: presumption of denial for exports

            **Treaty Quick Facts**
            - INF (1987–2019): banned ground-launched missiles 500–5,500 km
            - New START: limits to 1,550 deployed strategic warheads
            """
        )

    st.sidebar.markdown(
        f"<div style='padding:12px 0 4px; font-size:0.70rem; color:#6B6F84; text-align:center;'>"
        f"Open-source defense research<br>All data from public sources"
        f"</div>",
        unsafe_allow_html=True,
    )

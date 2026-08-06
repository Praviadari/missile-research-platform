"""
admin/admin_dashboard.py
=========================
Admin-only dashboard for the Missile Research Platform.

Shows:
  - User stats (total, by tier, recent signups)
  - Page view analytics
  - Data file integrity checks
  - Active A/B experiments
  - System health

Enterprise-gated: only admin user IDs defined in ADMIN_USER_IDS env var.
"""

import json
import os
import streamlit as st

from ui.theme import card, badge, section_header, metric_box


def render():
    st.title("🛠️ Admin Dashboard")
    st.caption("Internal admin view — visible only to admin users.")

    tab_health, tab_data, tab_experiments, tab_users = st.tabs([
        "🏥 Health", "📦 Data", "🧪 Experiments", "👥 Users"
    ])

    with tab_health:
        _render_health()
    with tab_data:
        _render_data_integrity()
    with tab_experiments:
        _render_experiments()
    with tab_users:
        _render_users()


def _render_health():
    st.markdown(section_header("🏥 System Health"), unsafe_allow_html=True)

    import asyncio
    try:
        from monitoring.health import health_check
        health = asyncio.run(health_check())

        overall = health.get("status", "unknown")
        color   = {"ok": "success", "degraded": "warning", "error": "danger"}.get(overall, "muted")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                metric_box("💚" if overall == "ok" else "⚠️", overall.upper(), "Overall Status"),
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                metric_box("⏱️", f"{health.get('uptime_s', 0):.0f}s", "Uptime"),
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                metric_box("🏷️", health.get("version", "—"), "Version"),
                unsafe_allow_html=True,
            )

        st.markdown(sub_header("Dependency Checks"), unsafe_allow_html=True)
        for name, check in health.get("checks", {}).items():
            status = check.get("status", "unknown")
            bv     = {"ok": "success", "skipped": "muted", "error": "danger"}.get(status, "warning")
            reason = check.get("reason", "")
            st.markdown(
                card(
                    f"<strong>{name}</strong>  {badge(status, bv)}"
                    + (f"<br><span style='font-size:0.8rem;color:#E74C3C'>{reason}</span>" if reason else ""),
                    variant="plain",
                ),
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.error(f"Health check failed: {e}")


def _render_data_integrity():
    st.markdown(section_header("📦 Data File Integrity"), unsafe_allow_html=True)

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    files = {
        "missiles.json":          "Missile & interceptor database",
        "historical_events.json": "Historical strike events",
        "treaties.json":          "Arms control treaties",
        "resources.json":         "Academic resource library",
    }

    total_ok = 0
    for filename, description in files.items():
        path = os.path.join(data_dir, filename)
        try:
            with open(path) as f:
                data = json.load(f)
            count = len(data)
            size  = os.path.getsize(path)
            st.markdown(
                card(
                    f"✅ <strong>{filename}</strong>  {badge(str(count) + ' entries', 'success')}<br>"
                    f"<span style='font-size:0.8rem;color:#6B6F84'>{description} · {size:,} bytes</span>",
                    variant="success",
                ),
                unsafe_allow_html=True,
            )
            total_ok += 1
        except Exception as e:
            st.markdown(
                card(f"❌ <strong>{filename}</strong><br>{e}", variant="danger"),
                unsafe_allow_html=True,
            )

    st.metric("Data files OK", f"{total_ok}/{len(files)}")


def _render_experiments():
    st.markdown(section_header("🧪 A/B Experiments"), unsafe_allow_html=True)
    try:
        from abtest.experiments import list_active_experiments, EXPERIMENTS
        active = list_active_experiments()

        st.markdown(
            f"<span style='color:#6B6F84;'>{len(active)} active · "
            f"{sum(1 for e in EXPERIMENTS.values() if not e.get('active'))} paused</span>",
            unsafe_allow_html=True,
        )

        for exp in active:
            with st.expander(f"🧪 **{exp['name']}**", expanded=False):
                st.markdown(f"**Description:** {exp['description']}")
                st.markdown(f"**Variants:** {', '.join(exp['variants'])}")
                st.markdown(f"**Your variant (admin):** {badge(exp['variant'], 'info')}", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Experiment data unavailable: {e}")


def _render_users():
    st.markdown(section_header("👥 User Management"), unsafe_allow_html=True)

    try:
        from database.session import tier_counts

        counts = tier_counts()
    except Exception:
        counts = {}

    if counts:
        cols = st.columns(max(len(counts), 1))
        for i, (tier, n) in enumerate(sorted(counts.items())):
            with cols[i % len(cols)]:
                st.markdown(
                    metric_box("👤", str(n), f"{tier} users"),
                    unsafe_allow_html=True,
                )
        st.caption("Counts from local/platform database (`users` table).")
    else:
        st.markdown(
            card(
                "No durable user rows yet. Set <code>DATABASE_URL</code> and sign in "
                "users (or run migrations) to populate tier counts.",
                variant="info",
            ),
            unsafe_allow_html=True,
        )

    if not os.getenv("SUPABASE_URL"):
        st.markdown(
            card(
                "🔧 <strong>Dev mode:</strong> Supabase admin directory is unavailable "
                "without <code>SUPABASE_URL</code>.",
                variant="warning",
            ),
            unsafe_allow_html=True,
        )
    else:
        st.caption(
            "Supabase Auth user directory still requires SUPABASE_SERVICE_ROLE_KEY "
            "for full account management (not exposed in this UI)."
        )


def sub_header(text: str) -> str:
    return f"<div class='mp-sub-header'>{text}</div>"

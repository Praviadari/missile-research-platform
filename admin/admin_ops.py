"""
admin/admin_ops.py
==================
GrowthOps admin page — conversion funnel and user acquisition analytics.

Shows:
  - Free → Pro conversion funnel
  - Page engagement ranked by time-on-page
  - Feature adoption rates by tier
  - A/B experiment quick-toggle

Admin-only page.
"""

import streamlit as st
from ui.theme import card, badge, section_header


def render():
    st.title("⚙️ GrowthOps")
    st.caption("Conversion analytics and growth operations. Admin only.")

    tab_funnel, tab_engagement, tab_abtest = st.tabs([
        "📈 Conversion Funnel", "📊 Page Engagement", "🧪 Experiment Control"
    ])

    with tab_funnel:
        _render_funnel()
    with tab_engagement:
        _render_engagement()
    with tab_abtest:
        _render_abtest_control()


def _render_funnel():
    st.markdown(section_header("📈 Free → Pro Conversion Funnel"), unsafe_allow_html=True)

    if not _posthog_available():
        st.markdown(
            card(
                "📊 <strong>Analytics not configured.</strong> "
                "Set POSTHOG_API_KEY to enable funnel analytics. "
                "Below is the funnel structure — wire each step to PostHog events.",
                variant="info",
            ),
            unsafe_allow_html=True,
        )

    funnel_steps = [
        ("Visitors",              "page_view",           100),
        ("DB Browser opened",     "page_view.missile_database", 72),
        ("Pro page hit (gated)",  "gate_shown",          31),
        ("Upgrade CTA clicked",   "upgrade_clicked",     18),
        ("Stripe checkout opened","stripe_checkout",     12),
        ("Subscription created",  "stripe_subscription", 5),
    ]

    import plotly.graph_objects as go
    from ui.charts import apply_theme, COLORS

    labels  = [s[0] for s in funnel_steps]
    values  = [s[2] for s in funnel_steps]
    pcts    = [v / values[0] * 100 for v in values]

    fig = go.Figure(go.Funnel(
        y=labels, x=values,
        textinfo="value+percent initial",
        marker=dict(color=COLORS[:len(labels)]),
    ))
    fig.update_layout(**apply_theme(title="Conversion Funnel (mock data)"), height=360)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("⚠️ Mock data shown. Wire PostHog events to populate real numbers.")

    st.markdown(section_header("📋 Event Map"), unsafe_allow_html=True)
    for name, event, _ in funnel_steps:
        st.markdown(
            card(f"<strong>{name}</strong>  →  <code>{event}</code>", variant="plain"),
            unsafe_allow_html=True,
        )


def _render_engagement():
    st.markdown(section_header("📊 Page Engagement"), unsafe_allow_html=True)

    pages = [
        ("missile_database",    "Missile Database",    "Free", 4.2, 82),
        ("historical_timeline", "Historical Timeline", "Free", 3.8, 67),
        ("learning_center",     "Learning Center",     "Free", 6.1, 44),
        ("treaty_guide",        "Treaty Guide",        "Free", 2.9, 38),
        ("resource_library",    "Resource Library",    "Free", 1.8, 22),
        ("trajectory",          "Trajectory Sim",      "Pro",  7.4, 18),
        ("design_lab",          "Design Lab",          "Pro",  9.2, 14),
        ("defense_lab",         "Defense Lab",         "Pro",  5.5, 11),
    ]

    import pandas as pd
    df = pd.DataFrame(pages, columns=["key", "Page", "Tier", "Avg Time (min)", "Sessions"])
    df_display = df[["Page", "Tier", "Avg Time (min)", "Sessions"]].copy()
    st.dataframe(df_display, use_container_width=True)
    st.caption("⚠️ Mock engagement data. Connect PostHog for real figures.")


def _render_abtest_control():
    st.markdown(section_header("🧪 Experiment Control Panel"), unsafe_allow_html=True)

    try:
        from abtest.experiments import EXPERIMENTS

        for name, exp in EXPERIMENTS.items():
            with st.expander(f"{'✅' if exp.get('active') else '⏸️'} **{name}**"):
                st.markdown(f"**Description:** {exp.get('description','—')}")
                st.markdown(f"**Variants:** {', '.join(exp.get('variants',[]))}")
                st.markdown(f"**Traffic:** {exp.get('traffic',0)*100:.0f}% of users")
                status = "active" if exp.get("active") else "paused"
                st.markdown(f"**Status:** {badge(status, 'success' if status=='active' else 'muted')}", unsafe_allow_html=True)
                st.caption("Toggle experiments by editing abtest/experiments.py — EXPERIMENTS dict.")
    except Exception as e:
        st.error(f"Experiment registry unavailable: {e}")


def _posthog_available() -> bool:
    import os
    return bool(os.getenv("POSTHOG_API_KEY"))

"""
modules/missile_database.py
============================
Read-only missile and interceptor database browser.

Displays publicly documented specifications for 32+ systems.
All data sourced from CSIS, IISS, Janes, US DoD reports, and NTI.

Public page — no authentication required.
"""

import json
import os
import streamlit as st
import pandas as pd

from ui.theme import card, badge, section_header, sub_header, metric_box
from ui.charts import (
    range_comparison_chart,
    payload_vs_range_scatter,
    mach_comparison_chart,
    country_distribution_pie,
)

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "missiles.json")


@st.cache_data
def _load_missiles():
    with open(_DATA_PATH) as f:
        return json.load(f)


CATEGORY_ORDER = ["SRBM", "MRBM", "IRBM", "ICBM", "ADV-BM", "Hypers", "Cruise", "Anti-Ship", "Loitering", "Interceptor"]
CATEGORY_LABELS = {
    "SRBM":       "Short-Range Ballistic (SRBM, < 1,000 km)",
    "MRBM":       "Medium-Range Ballistic (MRBM, 1,000–3,000 km)",
    "IRBM":       "Intermediate-Range Ballistic (IRBM, 3,000–5,500 km)",
    "ICBM":       "Intercontinental Ballistic (ICBM, > 5,500 km)",
    "ADV-BM":     "Advanced Ballistic (maneuvering reentry vehicle)",
    "Hypers":     "Hypersonic Glide / Scramjet (Mach 5+)",
    "Cruise":     "Cruise Missile (subsonic / supersonic)",
    "Anti-Ship":  "Anti-Ship Missile",
    "Loitering":  "Loitering Munition / UAS",
    "Interceptor":"Missile Defense Interceptor",
}


def render():
    st.title("📋 Missile & Interceptor Database")
    st.caption(
        "Technical specifications drawn from public sources: CSIS, IISS, Janes, "
        "NTI, and declassified US DoD reports. Uncertain values marked ⚠️."
    )

    missiles = _load_missiles()

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.expander("🔍 Filters", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            all_cats = sorted(set(m.get("category", "Other") for m in missiles))
            sel_cats = st.multiselect(
                "Category",
                all_cats,
                default=[c for c in all_cats if c != "Interceptor"],
            )
        with col2:
            all_countries = sorted(set(m.get("country", "Other") for m in missiles))
            sel_countries = st.multiselect("Country / Origin", all_countries, default=all_countries)
        with col3:
            max_range = max(m.get("range_km", 0) for m in missiles if isinstance(m.get("range_km"), (int, float)))
            range_filter = st.slider("Max Range (km)", 0, int(max_range) + 500, int(max_range) + 500, step=100)
        with col4:
            show_interceptors = st.checkbox("Include Interceptors", value=True)
            show_uncertain = st.checkbox("Show ⚠️ Uncertain Specs", value=True)

    # Apply filters
    filtered = [
        m for m in missiles
        if m.get("category") in sel_cats
        and m.get("country") in sel_countries
        and (isinstance(m.get("range_km"), (int, float)) and m.get("range_km", 0) <= range_filter
             or m.get("category") == "Interceptor")
        and (show_interceptors or m.get("category") != "Interceptor")
        and (show_uncertain or not m.get("_uncertain", False))
    ]

    st.markdown(
        f"<span style='color:#6B6F84; font-size:0.85rem;'>"
        f"Showing <strong style='color:#E8E8F0;'>{len(filtered)}</strong> of "
        f"{len(missiles)} systems</span>",
        unsafe_allow_html=True,
    )

    # ── View toggle ───────────────────────────────────────────────────────────
    view = st.radio("View", ["📋 Table", "🃏 Cards", "📊 Charts"], horizontal=True)

    if view == "📋 Table":
        _render_table(filtered)
    elif view == "🃏 Cards":
        _render_cards(filtered)
    else:
        _render_charts(filtered)


def _render_table(missiles):
    rows = []
    for m in missiles:
        uncertain = "⚠️ " if m.get("_uncertain") else ""
        rows.append({
            "System":        f"{uncertain}{m['name']}",
            "Country":       m.get("country", "—"),
            "Category":      m.get("category", "—"),
            "Range (km)":    m.get("range_km", "—"),
            "Payload (kg)":  m.get("payload_kg", "—"),
            "Propulsion":    m.get("propulsion", "—"),
            "Stages":        m.get("stages", "—"),
            "Peak Mach":     m.get("peak_mach", "—"),
            "CEP (m)":       m.get("cep_m", "—"),
            "Guidance":      ", ".join(m.get("guidance", ["—"])),
            "Operational":   "✅" if m.get("operational") else "🔬 Testing",
            "Since":         m.get("first_test", "—"),
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, height=480)
    else:
        st.info("No systems match the current filters.")


def _render_cards(missiles):
    # Group by category
    from collections import defaultdict
    grouped = defaultdict(list)
    for m in missiles:
        grouped[m.get("category", "Other")].append(m)

    for cat in CATEGORY_ORDER:
        ms = grouped.get(cat, [])
        if not ms:
            continue
        st.markdown(section_header(f"{CATEGORY_LABELS.get(cat, cat)} ({len(ms)})"), unsafe_allow_html=True)

        cols = st.columns(min(3, len(ms)))
        for i, m in enumerate(ms):
            with cols[i % 3]:
                uncertain = m.get("_uncertain", False)
                op_badge  = badge("Operational", "success") if m.get("operational") else badge("Testing", "warning")
                unc_badge = " " + badge("⚠️ Uncertain specs", "warning") if uncertain else ""

                st.markdown(
                    f"""
                    <div class='missile-card'>
                        <div class='missile-card-name'>🚀 {m['name']}</div>
                        <div style='margin:6px 0;'>
                            {badge(m.get('country',''), 'info')} &nbsp;
                            {badge(m.get('category',''), 'danger')} &nbsp;
                            {op_badge}{unc_badge}
                        </div>
                        <div style='font-size:0.82rem; color:#B8BCC8; line-height:1.9;'>
                            <strong>Range:</strong> {m.get('range_km','—'):,} km &nbsp;|&nbsp;
                            <strong>Payload:</strong> {str(m.get('payload_kg','—'))} kg<br>
                            <strong>Propulsion:</strong> {m.get('propulsion','—')} ({m.get('stages','?')} stage)<br>
                            <strong>Peak Mach:</strong> {m.get('peak_mach','—')} &nbsp;|&nbsp;
                            <strong>CEP:</strong> {str(m.get('cep_m','—'))} m<br>
                            <strong>Guidance:</strong> {', '.join(m.get('guidance', ['—']))}<br>
                            <strong>First test:</strong> {m.get('first_test','—')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.expander(f"ℹ️ Notes — {m['name']}", expanded=False):
                    st.markdown(m.get("status_notes", "No additional notes."))
                    st.markdown("**Sources:** " + "; ".join(m.get("sources", ["—"])))

        st.markdown("<br>", unsafe_allow_html=True)


def _render_charts(missiles):
    # Filter out interceptors for range charts (no payload/range like offensive missiles)
    offensive = [m for m in missiles if m.get("category") != "Interceptor"
                 and isinstance(m.get("range_km"), (int, float))]

    if not offensive:
        st.info("No offensive missile systems selected for charting.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "📏 Range Comparison", "💣 Payload vs Range", "💨 Mach Numbers", "🌍 By Country"
    ])

    with tab1:
        cats = list(set(m.get("category") for m in offensive))
        fig = range_comparison_chart(offensive, cats)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Source: CSIS Missile Defense Project, IISS Military Balance 2024")

    with tab2:
        fig = payload_vs_range_scatter(offensive)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Bubble positions show range-payload tradeoff. Hover for system name.")

    with tab3:
        fig = mach_comparison_chart(offensive)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Blue dashed line = Mach 5 hypersonic threshold.")

    with tab4:
        fig = country_distribution_pie(missiles)
        st.plotly_chart(fig, use_container_width=True)

    # ── Summary metrics ───────────────────────────────────────────────────────
    st.divider()
    st.markdown(sub_header("Database Summary Statistics"), unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Systems shown", len(missiles))
    if offensive:
        col2.metric("Max range", f"{max(m.get('range_km',0) for m in offensive):,} km")
        col3.metric("Max payload", f"{max(m.get('payload_kg',0) for m in offensive if isinstance(m.get('payload_kg'),(int,float))):,} kg")
        col4.metric("Max Mach", f"Mach {max(m.get('peak_mach',0) for m in offensive):.0f}")
        col5.metric("Hypersonic (Mach 5+)", sum(1 for m in offensive if m.get('peak_mach', 0) >= 5))

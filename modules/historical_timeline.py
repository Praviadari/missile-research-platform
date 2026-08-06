"""
modules/historical_timeline.py
================================
Interactive historical timeline of documented missile strike events.

All events drawn from publicly available journalistic, governmental,
and academic sources. Covers 2020–2024 with verified intercept data.

Public page — no authentication required.
"""

import json
import os
import streamlit as st

from ui.theme import card, badge, section_header, timeline_event
from ui.charts import escalation_timeline_chart

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "historical_events.json")


@st.cache_data
def _load_events():
    with open(_DATA_PATH) as f:
        return json.load(f)


def render():
    st.title("📅 Historical Missile Strike Timeline")
    st.caption(
        "Documented ballistic and cruise missile use in conflict, 2020–2024. "
        "All data from public journalistic, governmental, and academic sources. "
        "Casualty and intercept figures from official statements and verified reporting."
    )

    events = _load_events()

    # ── Escalation chart ──────────────────────────────────────────────────────
    st.markdown(section_header("📈 Escalation Overview"), unsafe_allow_html=True)

    # Build chart data from events with numeric missile counts
    chart_events = [
        {
            "label": f"{e['date'].split(',')[0]}\n{e['operation'][:20]}",
            "missiles_fired": e.get("missiles_fired", 0) if isinstance(e.get("missiles_fired"), int) else 0,
            "intercepted":    e.get("intercepted", 0)    if isinstance(e.get("intercepted"), int)    else 0,
        }
        for e in events
        if isinstance(e.get("missiles_fired"), int) and e.get("missiles_fired", 0) > 0
    ]
    if chart_events:
        fig = escalation_timeline_chart(chart_events)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Sources: IDF Spokesperson, US DoD, Reuters, BBC, "
            "CSIS Missile Defense Project, Congressional Research Service."
        )

    # ── Summary metrics ───────────────────────────────────────────────────────
    numeric_events = [e for e in events if isinstance(e.get("missiles_fired"), int)]
    total_fired    = sum(e.get("missiles_fired", 0) for e in numeric_events)
    total_intercep = sum(e.get("intercepted", 0)    for e in numeric_events
                         if isinstance(e.get("intercepted"), int))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Events Documented", len(events))
    col2.metric("Total Projectiles (numeric events)", f"{total_fired:,}")
    col3.metric("Confirmed Intercepted", f"{total_intercep:,}")
    if total_fired > 0:
        col4.metric("Overall Intercept Rate", f"{total_intercep/total_fired*100:.0f}%")

    st.divider()

    # ── Filter ────────────────────────────────────────────────────────────────
    st.markdown(section_header("🗂️ Event Details"), unsafe_allow_html=True)
    actors = sorted(set(e.get("actor", "Unknown").split("(")[0].strip() for e in events))
    sel_actor = st.selectbox("Filter by actor", ["All"] + actors)

    filtered = events if sel_actor == "All" else [
        e for e in events if sel_actor.lower() in e.get("actor", "").lower()
    ]

    # ── Event expanders ───────────────────────────────────────────────────────
    for ev in filtered:
        fired     = ev.get("missiles_fired", "Unknown")
        intercept = ev.get("intercepted", "Unknown")
        rate_str  = ""
        if isinstance(fired, int) and isinstance(intercept, int) and fired > 0:
            rate_str = f" ({intercept/fired*100:.0f}% intercepted)"

        with st.expander(
            f"**{ev['date']}** — {ev['operation']}",
            expanded=False,
        ):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Actor:** {ev.get('actor','—')}")
                st.markdown(f"**Target:** {ev.get('target','—')}")
            with c2:
                st.markdown(f"**Projectiles fired:** {fired}")
                st.markdown(f"**Intercepted:** {intercept}{rate_str}")
            with c3:
                st.markdown(f"**Type:** {ev.get('type','—')}")
                cas = ev.get("casualties", "—")
                cas_color = "danger" if isinstance(cas, int) and cas > 0 else "muted"
                st.markdown(
                    f"**Casualties:** {badge(str(cas), cas_color)}",
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown(f"**Context:** {ev.get('context','')}")

            if ev.get("significance"):
                st.markdown(
                    card(f"📌 <strong>Strategic significance:</strong> {ev['significance']}", variant="info"),
                    unsafe_allow_html=True,
                )

            if ev.get("intercept_rate_pct"):
                st.progress(
                    ev["intercept_rate_pct"] / 100,
                    text=f"Intercept rate: {ev['intercept_rate_pct']:.1f}%"
                )

            st.markdown(
                f"<div style='color:#6B6F84; font-size:0.78rem; margin-top:8px;'>"
                f"📚 Sources: {'; '.join(ev.get('sources', ['—']))}"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Methodological note ───────────────────────────────────────────────────
    st.divider()
    st.markdown(
        card(
            "📝 <strong>Methodological note:</strong> Intercept and casualty figures shown here "
            "reflect official statements and verified reporting at the time of writing. "
            "Battle damage assessments evolve over time as additional information emerges. "
            "Where official figures from multiple governments differ, we present the most "
            "widely corroborated estimate and note the discrepancy. All events involve "
            "significant fog-of-war uncertainty.",
            variant="plain",
        ),
        unsafe_allow_html=True,
    )

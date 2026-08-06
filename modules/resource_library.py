"""
modules/resource_library.py
============================
Curated bibliography of public-domain and open-access sources
for missile technology research and policy study.

Public page — no authentication required.
"""

import json
import os
import streamlit as st

from ui.theme import card, badge, section_header

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "resources.json")


@st.cache_data
def _load_resources():
    with open(_DATA_PATH) as f:
        return json.load(f)


TYPE_ICONS = {
    "Reference Database":   "🗄️",
    "Annual Reference":     "📅",
    "Policy Reference":     "📜",
    "Official Government Report": "🏛️",
    "Research Reports":     "🔬",
    "Research Database":    "🔍",
    "Research Publication": "📰",
    "Academic Blog / Podcast": "🎙️",
    "Textbook":             "📚",
    "Professional Reference Database": "💼",
    "Academic Journal":     "📖",
    "Monograph":            "📋",
    "Reference":            "📄",
}

ACCESS_BADGE = {
    "Free": "success",
    "Subscription (libraries often provide free access)": "info",
    "Subscription (Tandfonline); many articles available free after embargo": "info",
    "Subscription (expensive; available via many research libraries)": "warning",
    "Purchase required (~$100)": "warning",
    "Purchase required": "warning",
    "Purchase / library": "muted",
    "Library / purchase": "muted",
}


def render():
    st.title("📖 Resource Library")
    st.caption(
        "Curated bibliography of the best public-domain and open-access sources "
        "for missile technology study and arms control policy research."
    )

    resources = _load_resources()

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        types = sorted(set(r.get("type", "Other") for r in resources))
        sel_types = st.multiselect("Filter by type", types, default=types)
    with col2:
        search = st.text_input("🔍 Search resources", placeholder="e.g. Iran, propulsion, treaty…")

    filtered = [
        r for r in resources
        if r.get("type") in sel_types
        and (not search or search.lower() in r.get("title","").lower()
             or search.lower() in r.get("description","").lower()
             or any(search.lower() in t.lower() for t in r.get("topics", [])))
    ]

    st.markdown(
        f"<span style='color:#6B6F84; font-size:0.85rem;'>"
        f"Showing <strong style='color:#E8E8F0;'>{len(filtered)}</strong> of "
        f"{len(resources)} resources</span>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Resource cards ────────────────────────────────────────────────────────
    for r in filtered:
        icon   = TYPE_ICONS.get(r.get("type",""), "📄")
        access = r.get("access", "")
        av     = ACCESS_BADGE.get(access, "muted")

        with st.expander(f"{icon} **{r['title']}**  ·  {badge(access, av)}", expanded=False):
            col_l, col_r = st.columns([3, 1])
            with col_l:
                if r.get("organization"):
                    st.markdown(f"**Organization:** {r['organization']}")
                if r.get("authors"):
                    st.markdown(f"**Authors:** {', '.join(r['authors'])}")
                if r.get("publisher"):
                    st.markdown(f"**Publisher:** {r.get('publisher')} ({r.get('year','')})")
                st.markdown(f"**Type:** {r.get('type','—')}")
                st.markdown(r.get("description",""))

            with col_r:
                if r.get("topics"):
                    st.markdown("**Topics:**")
                    for t in r["topics"]:
                        st.markdown(f"- {t}")

            if r.get("url"):
                st.markdown(f"🔗 [{r['url']}]({r['url']})")

    # ── How to access section ─────────────────────────────────────────────────
    st.divider()
    st.markdown(section_header("🔑 Access Tips"), unsafe_allow_html=True)
    st.markdown(
        card(
            "<strong>Free access strategies for subscription resources:</strong><br><br>"
            "• <strong>University library access:</strong> If you're affiliated with a university, "
            "your library almost certainly subscribes to IISS Military Balance, Janes, and major journals. "
            "Access through your library portal.<br><br>"
            "• <strong>Interlibrary loan:</strong> Public library members can request academic papers "
            "and books via interlibrary loan — usually free.<br><br>"
            "• <strong>Open access versions:</strong> Many academic papers are available on "
            "ResearchGate, Academia.edu, or authors' institutional pages. Search the title + 'PDF'.<br><br>"
            "• <strong>Government reports:</strong> All US DoD reports listed here are freely available "
            "from defense.gov. Congressional Research Service reports available via everycrsreport.com.",
            variant="info",
        ),
        unsafe_allow_html=True,
    )

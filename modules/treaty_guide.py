"""
modules/treaty_guide.py
========================
Interactive browser for major arms control treaties and export control regimes.

Covers: NPT, INF, New START, MTCR, CWC, Hague Code of Conduct, AUKUS.
Includes an MTCR threshold checker tool.

Public page — no authentication required.
"""

import json
import os
import streamlit as st

from ui.theme import card, badge, section_header, sub_header
from ui.charts import treaty_timeline_chart

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "treaties.json")


@st.cache_data
def _load_treaties():
    with open(_DATA_PATH) as f:
        return json.load(f)


STATUS_BADGE = {
    "In force":              "success",
    "Active":                "success",
    "Active (voluntary)":    "info",
    "Suspended by Russia (Feb 2023)": "warning",
    "Terminated":            "danger",
    "Expired":               "muted",
}

CATEGORY_ICONS = {
    "Nuclear Non-Proliferation":  "☢️",
    "Bilateral Arms Control":     "🤝",
    "Strategic Nuclear Arms Control": "🛡️",
    "Export Control Regime":      "📦",
    "WMD Non-Proliferation":      "⚗️",
    "Transparency Measure":       "🔍",
    "Alliance / Capability Sharing": "🌐",
}


def render():
    st.title("📜 Treaty & Arms Control Policy Guide")
    st.caption(
        "Key arms control treaties, export control regimes, and relevant policy frameworks. "
        "All content from public governmental, academic, and NGO sources."
    )

    treaties = _load_treaties()

    # ── Timeline ──────────────────────────────────────────────────────────────
    st.markdown(section_header("📈 Arms Control Treaty Timeline"), unsafe_allow_html=True)
    fig = treaty_timeline_chart()
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Sources: US Department of State, Arms Control Association, UN Office for Disarmament Affairs."
    )

    st.divider()

    # ── MTCR Threshold Checker ────────────────────────────────────────────────
    st.markdown(section_header("📦 MTCR Threshold Checker"), unsafe_allow_html=True)
    st.markdown(
        "The Missile Technology Control Regime controls exports of missile systems capable "
        "of delivering ≥500 kg to ≥300 km. Enter specifications to check which MTCR "
        "category would apply."
    )

    col1, col2 = st.columns(2)
    with col1:
        payload_kg = st.number_input("Payload (kg)", min_value=0, max_value=10000, value=500, step=50)
    with col2:
        range_km = st.number_input("Range (km)", min_value=0, max_value=20000, value=300, step=50)

    if payload_kg >= 500 and range_km >= 300:
        st.markdown(
            card(
                "🔴 <strong>MTCR Category I</strong> — This system meets both thresholds "
                f"(payload ≥500 kg: <strong>{payload_kg} kg</strong>, range ≥300 km: "
                f"<strong>{range_km} km</strong>). "
                "MTCR members apply a presumption of denial for export licenses. "
                "Transfer to non-MTCR states requires extraordinary justification and is "
                "rarely approved. This category includes all ballistic missiles capable of "
                "delivering nuclear, chemical, or biological weapons.",
                variant="danger",
            ),
            unsafe_allow_html=True,
        )
    elif range_km >= 300 or payload_kg >= 500:
        st.markdown(
            card(
                "🟡 <strong>MTCR Category II</strong> — This system meets one threshold but not both. "
                "MTCR members review exports on a case-by-case basis. "
                "Controls still apply to subsystems, components, and propellant production equipment "
                "even if the complete system falls below Category I thresholds.",
                variant="warning",
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            card(
                "🟢 <strong>Below MTCR thresholds</strong> — This system (payload: "
                f"{payload_kg} kg, range: {range_km} km) does not meet the Category I "
                "threshold of ≥500 kg payload AND ≥300 km range. Note: subsystems and "
                "components may still be controlled under Category II. MTCR is advisory — "
                "individual member states may apply stricter controls.",
                variant="success",
            ),
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Treaty filter ─────────────────────────────────────────────────────────
    st.markdown(section_header("📋 Treaty Browser"), unsafe_allow_html=True)

    categories = sorted(set(t.get("category", "Other") for t in treaties))
    sel_cat = st.selectbox("Filter by category", ["All categories"] + categories)

    filtered = treaties if sel_cat == "All categories" else [
        t for t in treaties if t.get("category") == sel_cat
    ]

    for treaty in filtered:
        icon    = CATEGORY_ICONS.get(treaty.get("category", ""), "📄")
        status  = treaty.get("status", "Unknown")
        bv      = STATUS_BADGE.get(status, "muted")

        with st.expander(
            f"{icon} **{treaty['name']}**  |  {badge(status, bv)}",
            expanded=False,
        ):
            col_l, col_r = st.columns([2, 1])
            with col_l:
                st.markdown(f"**Full name:** {treaty.get('full_name', treaty['name'])}")
                st.markdown(treaty.get("summary", ""))

            with col_r:
                st.markdown("**Key facts:**")
                if treaty.get("signed"):
                    st.markdown(f"- Signed: **{treaty['signed']}**")
                if treaty.get("entered_into_force"):
                    st.markdown(f"- In force: **{treaty['entered_into_force']}**")
                if treaty.get("terminated"):
                    st.markdown(f"- Terminated: **{treaty['terminated']}**")
                if treaty.get("member_count") is not None:
                    st.markdown(f"- Members / parties: **{treaty['member_count']}**")
                elif treaty.get("members"):
                    members = treaty["members"]
                    label = ", ".join(members) if isinstance(members, list) else str(members)
                    st.markdown(f"- Members: **{label}**")
                elif treaty.get("parties"):
                    st.markdown(f"- Parties: **{treaty['parties']}**")
                if treaty.get("members"):
                    st.markdown(f"- Members: **{treaty['members']}**")

            # Treaty-specific detail sections
            if treaty.get("limits"):
                st.markdown(sub_header("⚖️ Treaty Limits"), unsafe_allow_html=True)
                for k, v in treaty["limits"].items():
                    st.markdown(f"- **{k.replace('_',' ').title()}:** {v:,}")

            if treaty.get("thresholds"):
                st.markdown(sub_header("📦 Control Thresholds"), unsafe_allow_html=True)
                for k, v in treaty["thresholds"].items():
                    st.markdown(f"- **{k}:** {v}")

            if treaty.get("key_articles"):
                st.markdown(sub_header("📖 Key Articles"), unsafe_allow_html=True)
                for art, text in treaty["key_articles"].items():
                    st.markdown(f"- **{art}:** {text}")

            if treaty.get("current_challenges"):
                st.markdown(sub_header("⚠️ Current Challenges"), unsafe_allow_html=True)
                for ch in treaty["current_challenges"]:
                    st.markdown(f"- {ch}")

            if treaty.get("missile_relevance"):
                st.markdown(
                    card(f"🚀 <strong>Missile relevance:</strong> {treaty['missile_relevance']}", variant="info"),
                    unsafe_allow_html=True,
                )

            if treaty.get("timeline"):
                st.markdown(sub_header("📅 Timeline"), unsafe_allow_html=True)
                for year, event in treaty["timeline"].items():
                    st.markdown(f"- **{year}:** {event}")

            if treaty.get("current_status_2025"):
                st.markdown(
                    card(f"📍 <strong>Current status (2025–26):</strong> {treaty['current_status_2025']}", variant="warning"),
                    unsafe_allow_html=True,
                )

            if treaty.get("non_parties"):
                st.markdown(
                    f"**Notable non-parties:** {', '.join(treaty['non_parties'])}"
                )

            st.markdown(
                f"<div style='color:#6B6F84; font-size:0.78rem; margin-top:8px;'>"
                f"📚 Source: {treaty.get('source','—')}"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Further reading ───────────────────────────────────────────────────────
    st.divider()
    st.markdown(section_header("📖 Further Reading"), unsafe_allow_html=True)
    st.markdown(
        card(
            "For comprehensive treaty text, status, and analysis:<br><br>"
            "• <strong>Arms Control Association</strong> — armscontrol.org/factsheets<br>"
            "• <strong>UN Office for Disarmament Affairs</strong> — un.org/disarmament<br>"
            "• <strong>US Department of State Arms Control</strong> — state.gov/arms-control<br>"
            "• <strong>SIPRI Yearbook</strong> — annual edition, available in most university libraries<br>"
            "• <strong>Nonproliferation Review</strong> — peer-reviewed journal (Tandfonline)",
            variant="info",
        ),
        unsafe_allow_html=True,
    )

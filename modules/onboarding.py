"""
modules/onboarding.py
=====================
Home / landing page for the Missile Analysis & Research Platform.

Introduces the platform's purpose, data sources, and navigation.
This is a public page — no authentication required.
"""

import streamlit as st
from ui.theme import card, badge, section_header, metric_box


def render():
    st.markdown(
        "<h1 style='font-size:2.2rem; font-weight:700; color:#E74C3C; margin-bottom:0.2rem;'>"
        "🚀 Missile Analysis & Research Platform"
        "</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='color:#6B6F84; font-size:1.05rem; margin-bottom:1.5rem;'>"
        "Open-source defense research — missile specifications, arms control policy, "
        "and historical analysis drawn entirely from public sources."
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.markdown(
        card(
            "⚠️ <strong>About this platform:</strong> All data is sourced exclusively from "
            "publicly available academic, governmental, and journalistic references — "
            "CSIS, IISS, Janes, NTI, US DoD reports, and peer-reviewed literature. "
            "This platform is intended for academic study, policy research, and "
            "educational purposes. It does not contain classified information.",
            variant="warning",
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Quick metrics ─────────────────────────────────────────────────────────
    st.markdown(section_header("📊 Platform Overview"), unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_box("🚀", "31", "Missile Systems\nin Database"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_box("📅", "8", "Historical\nStrike Events"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_box("📜", "8", "Arms Control\nTreaties"), unsafe_allow_html=True)
    with col4:
        st.markdown(metric_box("📖", "17", "Academic\nResources"), unsafe_allow_html=True)

    st.divider()

    # ── Navigation guide ──────────────────────────────────────────────────────
    st.markdown(section_header("🗺️ What's in this Platform"), unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### 📋 Missile Database (Free)")
        st.markdown(
            card(
                "Browse technical specifications for 31 missile and interceptor systems "
                "worldwide — Iran, US, Russia, China, Israel, North Korea. "
                "Filter by category, country, range, and propulsion type. "
                "All specs sourced from CSIS, IISS, Janes, and declassified US DoD reports.",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )
        if st.button("→ Open Missile Database", use_container_width=True):
            st.session_state["page"] = "missile_database"
            st.rerun()

        st.markdown("### 📅 Historical Timeline (Free)")
        st.markdown(
            card(
                "Documented history of ballistic and cruise missile use in conflict — "
                "from the Ain al-Assad strike (2020) through Operations True Promise I & II (2024) "
                "and the ongoing Ukraine conflict. Each event includes launch/intercept counts, "
                "context, and academic sources.",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )
        if st.button("→ Open Historical Timeline", use_container_width=True):
            st.session_state["page"] = "historical_timeline"
            st.rerun()

        st.markdown("### 📜 Treaty & Policy Guide (Free)")
        st.markdown(
            card(
                "Interactive browser for major arms control treaties: NPT, INF, "
                "New START, MTCR, CWC, Hague Code of Conduct, and AUKUS. "
                "Includes treaty texts, current status, compliance questions, "
                "and the MTCR threshold checker.",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )
        if st.button("→ Open Treaty Guide", use_container_width=True):
            st.session_state["page"] = "treaty_guide"
            st.rerun()

    with col_r:
        st.markdown("### 🎓 Learning Center (Free)")
        st.markdown(
            card(
                "Educational modules covering ballistic physics, rocket propulsion theory, "
                "guidance and accuracy, missile defense concepts, and historical context. "
                "Interactive charts and worked examples throughout.",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )
        if st.button("→ Open Learning Center", use_container_width=True):
            st.session_state["page"] = "learning_center"
            st.rerun()

        st.markdown("### 📖 Resource Library (Free)")
        st.markdown(
            card(
                "Curated bibliography of the best public-domain and open-access sources: "
                "CSIS Missile Defense Project, IISS Military Balance, NTI, SIPRI, "
                "38 North, Arms Control Association, Janes, and key academic textbooks.",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )
        if st.button("→ Open Resource Library", use_container_width=True):
            st.session_state["page"] = "resource_library"
            st.rerun()

        st.markdown(
            f"### ⚡ Pro Analysis Tools {badge('Pro', 'pro')}",
            unsafe_allow_html=True,
        )
        st.markdown(
            card(
                "Pro tier unlocks: trajectory simulation, propulsion analysis, "
                "reentry physics, hypersonic systems deep-dive, defense systems lab, "
                "3D visualization, and the 7-step missile design lab. "
                "All models use publicly documented physics equations.",
                variant="info",
            ),
            unsafe_allow_html=True,
        )
        if st.button("→ View Pro Features", type="primary", use_container_width=True):
            st.session_state["auth.show_auth_modal"] = True
            st.session_state["auth.auth_mode"] = "upgrade"
            st.rerun()

    st.divider()

    # ── Data sources ──────────────────────────────────────────────────────────
    st.markdown(section_header("📚 Data Sources & Methodology"), unsafe_allow_html=True)
    st.markdown(
        card(
            "<strong>All missile specifications</strong> in this database are drawn from a hierarchy of "
            "public sources: (1) US Department of Defense official reports, (2) CSIS Missile Defense Project, "
            "(3) IISS Military Balance, (4) Janes Defence Intelligence, (5) NTI, (6) peer-reviewed academic "
            "literature. Where specifications are uncertain or disputed, entries are marked with ⚠️ and "
            "alternative estimates are noted. No classified sources are used or implied.",
            variant="info",
        ),
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Primary References**")
        st.markdown(
            "- CSIS Missile Defense Project\n"
            "- IISS Military Balance (annual)\n"
            "- US DoD China/Russia/Iran Reports\n"
            "- Janes Land-Based Air Defence\n"
            "- NTI Country Profiles"
        )
    with col2:
        st.markdown("**Secondary References**")
        st.markdown(
            "- Arms Control Association\n"
            "- Federation of American Scientists\n"
            "- SIPRI Yearbook\n"
            "- 38 North (DPRK focus)\n"
            "- Congressional Research Service"
        )
    with col3:
        st.markdown("**Academic / Technical**")
        st.markdown(
            "- Nonproliferation Review\n"
            "- Sutton & Biblarz (propulsion)\n"
            "- Wertz SMAD (trajectory)\n"
            "- RAND Corporation studies\n"
            "- Arms Control Wonk"
        )

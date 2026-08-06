"""
modules/defense_lab.py
=======================
Defense systems reference — engagement envelopes, intercept kinematics,
layered defense architecture. Educational / research reference.

All system specifications from public sources:
  - US Missile Defense Agency public fact sheets
  - IISS Military Balance 2023
  - CSIS Missile Defense Project — missilethreat.csis.org
  - Congressional Budget Office: Ballistic Missile Defense (2021)

No targeting, no attack planning, no probability-of-kill modelling
tied to specific operational scenarios. Pure reference + education.

Pro-gated page.
"""

import math
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.theme import card, section_header, sub_header, badge
from ui.charts import apply_theme, COLORS
from utils.physics import closing_velocity, engagement_window_s

# ── Public-source interceptor data ────────────────────────────────────────────
INTERCEPTORS = {
    "Iron Dome (Tamir)": {
        "country": "Israel", "role": "Point defense",
        "max_altitude_km": 10, "max_range_km": 70,
        "target_types": ["rockets", "artillery", "mortars", "UAV"],
        "speed_ms": 900, "cost_k_usd": 50,
        "source": "Rafael Advanced Defense Systems; CSIS, 2023",
    },
    "David's Sling (Stunner)": {
        "country": "Israel", "role": "Medium-range air defense",
        "max_altitude_km": 15, "max_range_km": 300,
        "target_types": ["SRBM", "cruise missile", "aircraft"],
        "speed_ms": 2500, "cost_k_usd": 1000,
        "source": "Rafael/Raytheon; US DoD FY2024 budget",
    },
    "Arrow-2": {
        "country": "Israel", "role": "Endo/exo-atmospheric",
        "max_altitude_km": 50, "max_range_km": 150,
        "target_types": ["SRBM", "MRBM", "IRBM"],
        "speed_ms": 3000, "cost_k_usd": 3500,
        "source": "IAI; IISS Military Balance 2023",
    },
    "Arrow-3": {
        "country": "Israel", "role": "Exo-atmospheric",
        "max_altitude_km": 200, "max_range_km": 2400,
        "target_types": ["IRBM", "ICBM"],
        "speed_ms": 3000, "cost_k_usd": 3500,
        "source": "IAI; CSIS Missile Threat 2023",
    },
    "Patriot PAC-3 MSE": {
        "country": "USA", "role": "Endo-atmospheric TBM defense",
        "max_altitude_km": 30, "max_range_km": 35,
        "target_types": ["SRBM", "cruise missile", "aircraft"],
        "speed_ms": 1700, "cost_k_usd": 4000,
        "source": "Raytheon; MDA Fact Sheet 2023",
    },
    "THAAD": {
        "country": "USA", "role": "High-altitude endo/exo-atmospheric",
        "max_altitude_km": 200, "max_range_km": 200,
        "target_types": ["SRBM", "MRBM", "IRBM"],
        "speed_ms": 2800, "cost_k_usd": 11_000,
        "source": "Lockheed Martin; MDA Fact Sheet 2023",
    },
    "SM-3 Block IIA": {
        "country": "USA", "role": "Exo-atmospheric sea-based",
        "max_altitude_km": 1000, "max_range_km": 700,
        "target_types": ["MRBM", "IRBM"],
        "speed_ms": 4500, "cost_k_usd": 30_000,
        "source": "Raytheon; MDA Fact Sheet 2023",
    },
    "S-400 (40N6E)": {
        "country": "Russia", "role": "Long-range SAM",
        "max_altitude_km": 30, "max_range_km": 400,
        "target_types": ["aircraft", "cruise missile", "SRBM"],
        "speed_ms": 2000, "cost_k_usd": 500,
        "source": "IISS Military Balance 2023",
    },
    "HQ-9B (China)": {
        "country": "China", "role": "Long-range SAM",
        "max_altitude_km": 30, "max_range_km": 200,
        "target_types": ["aircraft", "cruise missile"],
        "speed_ms": 1700, "cost_k_usd": 300,
        "source": "IISS Military Balance 2023",
    },
}

LAYER_COLORS = {
    "Point defense":                "#3498DB",
    "Medium-range air defense":     "#2ECC71",
    "Endo/exo-atmospheric":         "#F39C12",
    "Exo-atmospheric":              "#E74C3C",
    "Endo-atmospheric TBM defense": "#9B59B6",
    "High-altitude endo/exo-atmospheric": "#1ABC9C",
    "Exo-atmospheric sea-based":    "#E67E22",
    "Long-range SAM":               "#95A5A6",
}


def render():
    st.title("🛡️ Defense Systems Lab")
    st.caption(
        "Air and missile defense reference — engagement envelopes, layered architecture, intercept kinematics. "
        "All system data from public sources (MDA, IISS, CSIS, Janes)."
    )

    tabs = st.tabs([
        "📊 Engagement Envelopes",
        "🏗️ Layered Architecture",
        "⚡ Intercept Kinematics",
        "💰 Cost Comparison",
        "📖 System Reference",
    ])
    with tabs[0]: _engagement_envelopes()
    with tabs[1]: _layered_architecture()
    with tabs[2]: _intercept_kinematics()
    with tabs[3]: _cost_comparison()
    with tabs[4]: _system_reference()


def _engagement_envelopes():
    st.markdown(section_header("📊 Engagement Envelope Comparison"), unsafe_allow_html=True)
    st.caption("Range vs altitude capabilities from public MDA and manufacturer fact sheets.")

    selected = st.multiselect(
        "Select systems",
        list(INTERCEPTORS.keys()),
        default=["Iron Dome (Tamir)", "Patriot PAC-3 MSE", "THAAD", "Arrow-3", "SM-3 Block IIA"],
    )
    if not selected:
        st.info("Select at least one system.")
        return

    fig = go.Figure()
    for i, name in enumerate(selected):
        sys = INTERCEPTORS[name]
        r   = sys["max_range_km"]
        h   = sys["max_altitude_km"]
        color = LAYER_COLORS.get(sys["role"], COLORS[i % len(COLORS)])

        # Draw engagement footprint as ellipse approximation
        theta_vals = [t * math.pi / 180 for t in range(0, 181, 5)]
        xs = [r * math.cos(t) for t in theta_vals]
        ys = [h * math.sin(t) for t in theta_vals]

        fig.add_trace(go.Scatter(
            x=xs, y=ys, name=name,
            mode="lines", fill="tozeroy",
            fillcolor=f"rgba({_hex_to_rgb(color)},0.07)",
            line=dict(color=color, width=2),
            hovertemplate=f"{name}<br>Max range: {r} km<br>Max alt: {h} km<extra></extra>",
        ))

    fig.update_layout(**apply_theme(title="Engagement Envelopes (Range vs Altitude)"),
                      height=400, showlegend=True)
    fig.update_xaxes(title_text="Slant Range (km)", gridcolor="#1E2235", zeroline=True,
                     zerolinecolor="#1E2235")
    fig.update_yaxes(title_text="Altitude (km)", gridcolor="#1E2235", zeroline=False,
                     rangemode="tozero")
    st.plotly_chart(fig, use_container_width=True)


def _layered_architecture():
    st.markdown(section_header("🏗️ Layered Defense Architecture"), unsafe_allow_html=True)
    st.markdown(
        "Modern air defense combines multiple interceptor layers at different "
        "ranges and altitudes to create overlapping coverage. The Israeli architecture "
        "is the most publicly documented multi-layer system."
    )

    layers = [
        ("Iron Dome",      "Short-range rockets,\nartillery, mortars",   "0–70 km",  "0–10 km",  COLORS[0]),
        ("David's Sling",  "SRBMs, cruise missiles,\nhigh-performance AC","0–300 km", "0–15 km",  COLORS[1]),
        ("Arrow-2",        "SRBMs, MRBMs,\nIRBMs (endo-exo)",           "0–150 km", "10–50 km", COLORS[4]),
        ("Arrow-3",        "IRBMs, ICBMs\n(exo-atmospheric)",            "0–2,400 km","50–200 km",COLORS[2]),
    ]

    for name, targets, rng, alt, color in layers:
        st.markdown(
            card(
                f"<div style='display:flex;align-items:center;gap:12px'>"
                f"<div style='background:{color}22;border-left:3px solid {color};padding:8px 14px;border-radius:6px;min-width:140px'>"
                f"<div style='color:{color};font-weight:700'>{name}</div>"
                f"<div style='font-size:0.78rem;color:#6B6F84'>{rng}<br>{alt}</div>"
                f"</div>"
                f"<div style='color:#B0B8D4;font-size:0.88rem'>{targets}</div>"
                f"</div>",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        card(
            "📌 <strong>Why layering matters:</strong> No single interceptor system achieves "
            "100% intercept probability. Multiple overlapping layers provide "
            "multiple engagement opportunities and cover different threat altitudes and speeds. "
            "The overlapping coverage also forces an attacker to consider multiple intercept "
            "opportunities rather than a single intercept window. "
            "<em>Source: CBO, 'Options for Deploying Missile Defenses in Europe' (2021)</em>",
            variant="info",
        ),
        unsafe_allow_html=True,
    )


def _intercept_kinematics():
    st.markdown(section_header("⚡ Intercept Kinematics"), unsafe_allow_html=True)
    st.markdown(
        "Closing speed and engagement window calculations. "
        "Reference: Zarchan, *Tactical and Strategic Missile Guidance*, 6th ed., AIAA 2012 Ch. 1."
    )

    col1, col2 = st.columns(2)
    with col1:
        t_speed = st.slider("Threat speed (m/s)", 500, 7000, 2500, step=100)
        t_angle = st.slider("Threat angle (°, 0=horizontal)", 0, 90, 45)
        slant_r = st.slider("Initial slant range (km)", 20, 500, 100)

    with col2:
        i_speed = st.slider("Interceptor speed (m/s)", 500, 5000, 2000, step=100)
        i_angle = st.slider("Interceptor angle (°)", 0, 90, 60)
        min_r   = st.slider("Min intercept range (km)", 1, 50, 5)

    vc  = closing_velocity(t_speed, t_angle, i_speed, i_angle)
    t_w = engagement_window_s(slant_r, vc, min_r)

    col1, col2, col3 = st.columns(3)
    col1.metric("Closing speed",       f"{vc:.0f} m/s  ({vc/1000*3600:.0f} km/h)")
    col2.metric("Engagement window",   f"{t_w:.1f} s")
    col3.metric("Relative Mach",       f"Mach {vc/340:.1f}")

    st.markdown(
        card(
            f"At a closing speed of <strong>{vc:.0f} m/s</strong>, the interceptor has "
            f"<strong>{t_w:.1f} seconds</strong> from current range {slant_r} km down to "
            f"minimum range {min_r} km. At Mach {t_w*t_speed/1000:.0f} km of threat travel "
            f"in that window, terminal guidance must be highly precise. "
            "This illustrates why high closing speeds (M>5 threats) compress engagement windows "
            "dramatically, challenging fire-control loop times.",
            variant="info" if t_w > 15 else "warning",
        ),
        unsafe_allow_html=True,
    )

    # Window vs range chart
    ranges = list(range(10, int(slant_r) + 20, 5))
    windows = [engagement_window_s(r, vc, min_r) for r in ranges]

    fig = go.Figure(go.Scatter(
        x=ranges, y=windows, mode="lines+markers",
        line=dict(color=COLORS[0], width=2),
        marker=dict(size=5),
        hovertemplate="Range: %{x} km<br>Window: %{y:.1f} s<extra></extra>",
    ))
    fig.add_vline(x=slant_r, line_dash="dot", line_color="#FFD700",
                  annotation_text="Current range", annotation_font_size=9)
    fig.update_layout(**apply_theme(title="Engagement Window vs Detection Range"),
                      height=300, showlegend=False)
    fig.update_xaxes(title_text="Slant Range (km)", gridcolor="#1E2235", zeroline=False)
    fig.update_yaxes(title_text="Available Window (s)", gridcolor="#1E2235", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)


def _cost_comparison():
    st.markdown(section_header("💰 Interceptor Cost Reference"), unsafe_allow_html=True)
    st.caption("Unit costs are public estimates from DoD budget documents and manufacturer statements.")

    names  = list(INTERCEPTORS.keys())
    costs  = [INTERCEPTORS[n]["cost_k_usd"] for n in names]
    ranges = [INTERCEPTORS[n]["max_range_km"] for n in names]
    roles  = [INTERCEPTORS[n]["role"] for n in names]
    short  = [n.split("(")[0].strip() for n in names]

    fig = go.Figure(go.Bar(
        x=short, y=costs,
        marker_color=[LAYER_COLORS.get(r, COLORS[0]) for r in roles],
        text=[f"${c:,}K" for c in costs],
        textposition="outside",
        hovertemplate="%{x}<br>Cost: $%{y:,}K<extra></extra>",
    ))
    fig.update_layout(**apply_theme(title="Interceptor Unit Cost (USD thousands)"),
                      height=360, showlegend=False)
    fig.update_yaxes(title_text="Unit Cost (USD thousands)", type="log",
                     gridcolor="#1E2235", zeroline=False)
    fig.update_xaxes(tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        card(
            "📌 <strong>Cost asymmetry:</strong> A SM-3 Block IIA costs ~$30M per interceptor. "
            "An Iron Dome Tamir missile costs ~$50K. This 600:1 ratio is why defense planners "
            "deploy layered architectures — using cheaper interceptors for shorter-range threats "
            "and more expensive systems only for high-altitude or long-range threats. "
            "The cost asymmetry relative to attacking weapons is a key concern in "
            "missile defense economics. "
            "<em>Source: CBO Report on Ballistic Missile Defense, Jan 2021</em>",
            variant="info",
        ),
        unsafe_allow_html=True,
    )


def _system_reference():
    st.markdown(section_header("📖 System Reference"), unsafe_allow_html=True)

    country_filter = st.selectbox("Filter by country",
                                  ["All"] + sorted(set(s["country"] for s in INTERCEPTORS.values())))

    for name, sys in INTERCEPTORS.items():
        if country_filter != "All" and sys["country"] != country_filter:
            continue
        color = LAYER_COLORS.get(sys["role"], "#6B6F84")
        with st.expander(f"**{name}**  —  {sys['country']}  •  {sys['role']}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Max range", f"{sys['max_range_km']} km")
            col2.metric("Max altitude", f"{sys['max_altitude_km']} km")
            col3.metric("Interceptor speed", f"{sys['speed_ms']:,} m/s")
            col1.metric("Unit cost (est.)", f"${sys['cost_k_usd']:,}K")

            tgt = ", ".join(sys["target_types"])
            st.markdown(f"**Target types:** {tgt}")
            st.caption(f"Source: {sys['source']}")


def _hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    return ",".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))

"""
modules/reentry_analysis.py
============================
Atmospheric reentry analysis — heating, deceleration, TPS materials.

Physics: Chapman entry analysis, Detra-Kemp-Riddell heat flux correlation,
         radiative equilibrium temperature.

References:
  - Chapman (1959) NASA TR R-11
  - Anderson, "Hypersonic and High Temperature Gas Dynamics", 2nd ed., AIAA 2006
  - Tauber & Sutton (1991), Journal of Spacecraft, 28(3)

Pro-gated page.
"""

import math
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.theme import card, section_header, sub_header, badge
from ui.charts import apply_theme, COLORS
from utils.physics import (
    ballistic_deceleration, stagnation_heat_flux,
    radiative_equilibrium_temp, isa_density, speed_of_sound_isa,
)

# ── TPS material reference data ───────────────────────────────────────────────
TPS_MATERIALS = {
    "PICA (Phenolic Impregnated Carbon Ablator)": {
        "max_temp_k":  3500, "density": 270, "k_w_mk": 0.30,
        "category": "Ablative", "used_on": "Dragon, Stardust, Mars rovers",
        "notes": "State-of-the-art ablator. Excellent for high heat loads.",
    },
    "AVCOAT (Apollo)": {
        "max_temp_k":  3300, "density": 520, "k_w_mk": 0.25,
        "category": "Ablative", "used_on": "Apollo CM, Orion",
        "notes": "Honeycomb-filled ablator. Being revived for Orion.",
    },
    "TUFI Ceramic Tiles (Shuttle)": {
        "max_temp_k":  1700, "density": 150, "k_w_mk": 0.07,
        "category": "Reusable ceramic", "used_on": "Space Shuttle orbiter",
        "notes": "Low density but fragile. Limited to moderate heat flux.",
    },
    "RCC (Reinforced Carbon-Carbon)": {
        "max_temp_k":  1922, "density": 1600, "k_w_mk": 6.30,
        "category": "Structural", "used_on": "Shuttle nose and wing edges",
        "notes": "Structural thermal protection. High conductivity.",
    },
    "C-PICA / 3D-CF ablator": {
        "max_temp_k":  3800, "density": 330, "k_w_mk": 0.35,
        "category": "Ablative", "used_on": "Research / next-gen RVs",
        "notes": "3D carbon fibre preform. Improved structural integrity.",
    },
    "Tungsten (nose tip)": {
        "max_temp_k":  3600, "density": 19_300, "k_w_mk": 170,
        "category": "Metallic", "used_on": "Nose tips, leading edges",
        "notes": "Very high melting point. Dense. Used for sharp leading edges.",
    },
}

# ── Reference reentry scenarios (all from public sources) ─────────────────────
REFERENCE_SCENARIOS = {
    "Apollo CM (lunar return)": {
        "beta": 390, "entry_angle": 6.5, "entry_velocity": 11_100,
        "source": "NASA SP-4205",
    },
    "Soyuz descent module": {
        "beta": 330, "entry_angle": 3.5, "entry_velocity": 7_700,
        "source": "Isakowitz, Space Launch Systems (1999)",
    },
    "Mars Science Lab aeroshell": {
        "beta": 146, "entry_angle": 15.5, "entry_velocity": 5_900,
        "source": "Vasavada et al., Space Science Reviews (2012)",
    },
    "Generic ICBM RV (public est.)": {
        "beta": 50_000, "entry_angle": 20.0, "entry_velocity": 7_000,
        "source": "Tewari, Atmospheric and Space Flight Dynamics (2007), Ch.10",
    },
    "Hypersonic glide body (HGB)": {
        "beta": 30_000, "entry_angle": 3.0, "entry_velocity": 6_000,
        "source": "RAND PE-243 (2017) — conceptual",
    },
}


def render():
    st.title("🌡️ Reentry Analysis")
    st.caption(
        "Atmospheric reentry heating, deceleration, and thermal protection. "
        "Chapman (1959), Detra-Kemp-Riddell correlation, Anderson (2006)."
    )

    tabs = st.tabs([
        "🔥 Heat & Deceleration",
        "🛡️ TPS Materials",
        "📊 Scenario Comparison",
        "📐 Theory",
    ])
    with tabs[0]: _heat_decel()
    with tabs[1]: _tps_materials()
    with tabs[2]: _scenario_compare()
    with tabs[3]: _theory()


def _heat_decel():
    st.markdown(section_header("🔥 Entry Heating & Deceleration Profile"), unsafe_allow_html=True)

    col_ctrl, col_ref = st.columns([2, 1])
    with col_ref:
        preset = st.selectbox("Load preset scenario", ["Custom"] + list(REFERENCE_SCENARIOS.keys()))

    defaults = REFERENCE_SCENARIOS.get(preset, {}) if preset != "Custom" else {}

    with col_ctrl:
        col1, col2 = st.columns(2)
        with col1:
            beta  = st.slider("Ballistic coefficient β (kg/m²)", 50, 80_000,
                               int(defaults.get("beta", 5000)), step=50)
            angle = st.slider("Entry angle (°)", 1.0, 30.0,
                               float(defaults.get("entry_angle", 10.0)), step=0.5)
        with col2:
            v_entry = st.slider("Entry velocity (m/s)", 3_000, 12_000,
                                int(defaults.get("entry_velocity", 7_000)), step=100)
            nose_r  = st.slider("Nose radius (m)", 0.05, 2.0, 0.20, step=0.05)

    if preset != "Custom" and "source" in defaults:
        st.caption(f"Source: {defaults['source']}")

    # Run simulation
    data = ballistic_deceleration(beta, angle, v_entry)

    alts   = [d["altitude_km"] for d in data]
    fluxes = [d["heat_flux_mw"] for d in data]
    temps  = [d["wall_temp_k"] for d in data]
    decels = [d["decel_g"] for d in data]
    machs  = [d["mach"] for d in data]
    vels   = [d["velocity_ms"] for d in data]

    peak_flux = max(fluxes)
    peak_temp = max(temps)
    peak_g    = max(decels)

    col1, col2, col3 = st.columns(3)
    col1.metric("Peak heat flux", f"{peak_flux:.2f} MW/m²")
    col2.metric("Peak wall temp", f"{peak_temp:.0f} K  ({peak_temp-273:.0f} °C)")
    col3.metric("Peak deceleration", f"{peak_g:.1f} g")

    fig = make_subplots(rows=2, cols=2,
        subplot_titles=("Heat Flux vs Altitude", "Wall Temperature vs Altitude",
                        "Deceleration vs Altitude", "Mach Number vs Altitude"),
        vertical_spacing=0.18, horizontal_spacing=0.12)

    fig.add_trace(go.Scatter(x=fluxes, y=alts, name="Heat Flux",
                             mode="lines", line=dict(color=COLORS[0], width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=temps, y=alts, name="Wall Temp",
                             mode="lines", line=dict(color=COLORS[3], width=2)), row=1, col=2)
    fig.add_trace(go.Scatter(x=decels, y=alts, name="Decel (g)",
                             mode="lines", line=dict(color=COLORS[1], width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=machs, y=alts, name="Mach",
                             mode="lines", line=dict(color=COLORS[4], width=2)), row=2, col=2)

    # TPS limit lines
    fig.add_vline(x=1.0, line_dash="dot", line_color="#E74C3C",
                  annotation_text="TUFI limit", annotation_font_size=8, row=1, col=1)
    fig.add_vline(x=1530, line_dash="dot", line_color="#E74C3C",
                  annotation_text="TUFI", annotation_font_size=8, row=1, col=2)

    fig.update_layout(**apply_theme(title="Reentry Profile"), height=560, showlegend=False)
    for (row, col), xlabel in [((1,1),"Heat Flux (MW/m²)"), ((1,2),"Wall Temp (K)"),
                                ((2,1),"Deceleration (g)"),  ((2,2),"Mach Number")]:
        fig.update_xaxes(title_text=xlabel, row=row, col=col,
                         gridcolor="#1E2235", zeroline=False)
        fig.update_yaxes(title_text="Altitude (km)", row=row, col=col,
                         gridcolor="#1E2235", zeroline=False)

    st.plotly_chart(fig, use_container_width=True)

    # TPS recommendation
    _recommend_tps(peak_flux, peak_temp)


def _recommend_tps(peak_flux_mw: float, peak_temp_k: float):
    st.markdown(sub_header("🛡️ TPS Recommendation"), unsafe_allow_html=True)
    suitable = []
    for name, mat in TPS_MATERIALS.items():
        if mat["max_temp_k"] >= peak_temp_k * 0.9:
            suitable.append((name, mat))

    if not suitable:
        st.markdown(
            card("⚠️ No standard TPS material can withstand the predicted peak temperature. "
                 "Active cooling or a very large nose radius would be required.", variant="danger"),
            unsafe_allow_html=True,
        )
        return

    for name, mat in suitable[:3]:
        margin = (mat["max_temp_k"] - peak_temp_k) / peak_temp_k * 100
        st.markdown(
            card(
                f"✅ <strong>{name}</strong> {badge(mat['category'], 'info')}<br>"
                f"Max temp: {mat['max_temp_k']:,} K · Margin: {margin:.0f}% · "
                f"Density: {mat['density']:,} kg/m³<br>"
                f"<span style='color:#6B6F84;font-size:0.82rem'>{mat['notes']}</span>",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )


def _tps_materials():
    st.markdown(section_header("🛡️ Thermal Protection System Materials"), unsafe_allow_html=True)

    for name, mat in TPS_MATERIALS.items():
        with st.expander(f"**{name}**  —  {mat['category']}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Max temp", f"{mat['max_temp_k']:,} K")
            col2.metric("Density", f"{mat['density']:,} kg/m³")
            col3.metric("Conductivity", f"{mat['k_w_mk']} W/m·K")
            st.markdown(f"**Used on:** {mat['used_on']}")
            st.markdown(f"**Notes:** {mat['notes']}")

    # Comparison chart
    names  = list(TPS_MATERIALS.keys())
    temps  = [TPS_MATERIALS[n]["max_temp_k"] for n in names]
    dens   = [TPS_MATERIALS[n]["density"] for n in names]
    short  = [n.split("(")[0].strip() for n in names]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Max Operating Temperature (K)", "Bulk Density (kg/m³)"))
    fig.add_trace(go.Bar(x=short, y=temps, marker_color=COLORS[0], name="Max Temp"), row=1, col=1)
    fig.add_trace(go.Bar(x=short, y=dens,  marker_color=COLORS[3], name="Density"),  row=1, col=2)
    fig.update_layout(**apply_theme(height=340), showlegend=False)
    fig.update_xaxes(tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)


def _scenario_compare():
    st.markdown(section_header("📊 Scenario Comparison"), unsafe_allow_html=True)

    selected = st.multiselect(
        "Select scenarios",
        list(REFERENCE_SCENARIOS.keys()),
        default=list(REFERENCE_SCENARIOS.keys())[:3],
    )
    if not selected:
        st.info("Select at least one scenario.")
        return

    import pandas as pd
    rows = []
    for name in selected:
        s    = REFERENCE_SCENARIOS[name]
        data = ballistic_deceleration(s["beta"], s["entry_angle"], s["entry_velocity"])
        peak_flux = max(d["heat_flux_mw"] for d in data)
        peak_temp = max(d["wall_temp_k"] for d in data)
        peak_g    = max(d["decel_g"] for d in data)
        rows.append({
            "Scenario":      name,
            "β (kg/m²)":    s["beta"],
            "Entry angle":   f"{s['entry_angle']}°",
            "Entry v (m/s)": s["entry_velocity"],
            "Peak flux (MW/m²)": f"{peak_flux:.2f}",
            "Peak temp (K)": f"{peak_temp:.0f}",
            "Peak G":        f"{peak_g:.1f}",
            "Source":        s["source"],
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # Heat flux trajectory overlay
    fig = go.Figure()
    for i, name in enumerate(selected):
        s    = REFERENCE_SCENARIOS[name]
        data = ballistic_deceleration(s["beta"], s["entry_angle"], s["entry_velocity"])
        fig.add_trace(go.Scatter(
            x=[d["heat_flux_mw"] for d in data],
            y=[d["altitude_km"] for d in data],
            name=name, mode="lines",
            line=dict(color=COLORS[i % len(COLORS)], width=2),
        ))
    fig.update_layout(**apply_theme(title="Heat Flux vs Altitude Comparison"),
                      height=380, showlegend=True)
    fig.update_xaxes(title_text="Heat Flux (MW/m²)", gridcolor="#1E2235", zeroline=False)
    fig.update_yaxes(title_text="Altitude (km)", gridcolor="#1E2235", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)


def _theory():
    st.markdown(section_header("📐 Theory"), unsafe_allow_html=True)
    st.markdown("### Chapman Entry Analysis (1959)")
    st.markdown(
        "Chapman's method provides closed-form solutions for entry velocity and deceleration "
        "in an exponential atmosphere. The velocity ratio u = v/vₑ is:"
    )
    st.latex(r"u = \exp\left(-\frac{\rho}{2\beta \sin\gamma}\right)")
    st.markdown("where ρ is local density, β = m/(C_D·A) is ballistic coefficient, γ is entry angle.")

    st.markdown("### Detra-Kemp-Riddell Heat Flux")
    st.latex(r"q_s = 1.83 \times 10^{-4} \sqrt{\frac{\rho}{R_n}} \cdot v^{3.15} \quad \text{[W/m²]}")

    st.markdown("### Radiative Equilibrium Temperature")
    st.latex(r"T_w = \left(\frac{q_s}{\varepsilon \sigma}\right)^{0.25}")

    st.markdown("""
    ### Ballistic Coefficient
    The ballistic coefficient β = m/(C_D · A) [kg/m²] governs how quickly a body decelerates:
    - **High β** (dense, blunt → streamlined RV): penetrates atmosphere deeply before decelerating.
      Peak heating at lower altitude; shorter peak-heating duration.
    - **Low β** (aeroshell, capsule): decelerates high in atmosphere.
      Longer heating duration; peak flux is lower but total heat load may be similar.

    ### References
    - Chapman, D.R., "An Approximate Analytical Method for Studying Entry into Planetary Atmospheres",
      NASA TR R-11, 1959
    - Anderson, J.D., "Hypersonic and High Temperature Gas Dynamics", 2nd ed., AIAA, 2006, Ch. 6–7
    - Tauber, M.E. & Sutton, K., "Stagnation-Point Radiative Heating Relations",
      Journal of Spacecraft and Rockets, 28(3), 1991
    """)

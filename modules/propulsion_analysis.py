"""
modules/propulsion_analysis.py
================================
Rocket propulsion analysis — Isp curves, staging optimisation, mass fraction explorer.

All physics from Sutton & Biblarz "Rocket Propulsion Elements", 9th ed. (2017).
Pro-gated page.
"""

import math
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.theme import card, section_header, sub_header, badge
from ui.charts import apply_theme, COLORS
from utils.physics import Stage, staging_analysis, isp_curve
from utils.units import tsiolkovsky_delta_v, G0, propellant_mass_fraction


# ── Propellant reference table ─────────────────────────────────────────────────
PROPELLANTS = {
    "Solid (AP/HTPB)":      {"isp_sl": 265, "isp_vac": 280, "density": 1750, "storable": True,  "toxic": False},
    "Solid (AP/Al/HTPB)":   {"isp_sl": 270, "isp_vac": 285, "density": 1800, "storable": True,  "toxic": False},
    "UDMH / N₂O₄":          {"isp_sl": 290, "isp_vac": 315, "density": 1200, "storable": True,  "toxic": True},
    "LOX / RP-1":            {"isp_sl": 295, "isp_vac": 340, "density": 1030, "storable": False, "toxic": False},
    "LOX / LH₂":             {"isp_sl": 380, "isp_vac": 450, "density":  360, "storable": False, "toxic": False},
    "N₂H₄ (monopropellant)": {"isp_sl": 185, "isp_vac": 220, "density":  800, "storable": True,  "toxic": True},
    "N₂ (cold gas)":         {"isp_sl":  60, "isp_vac":  70, "density":  800, "storable": True,  "toxic": False},
}


def render():
    st.title("🔥 Propulsion Analysis")
    st.caption(
        "Rocket propulsion performance tools. "
        "Equations: Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017)."
    )

    tabs = st.tabs([
        "⚗️ Propellant Explorer",
        "📐 Rocket Equation",
        "🔢 Staging Optimiser",
        "📊 Isp vs Altitude",
        "📖 Reference",
    ])

    with tabs[0]: _propellant_explorer()
    with tabs[1]: _rocket_equation_explorer()
    with tabs[2]: _staging_optimiser()
    with tabs[3]: _isp_altitude()
    with tabs[4]: _reference()


def _propellant_explorer():
    st.markdown(section_header("⚗️ Propellant Performance Comparison"), unsafe_allow_html=True)

    selected = st.multiselect(
        "Select propellants to compare",
        list(PROPELLANTS.keys()),
        default=["Solid (AP/HTPB)", "UDMH / N₂O₄", "LOX / RP-1", "LOX / LH₂"],
    )
    if not selected:
        st.info("Select at least one propellant.")
        return

    # Isp bar chart
    fig = go.Figure()
    isp_vacs = [PROPELLANTS[p]["isp_vac"] for p in selected]
    isp_sls  = [PROPELLANTS[p]["isp_sl"]  for p in selected]

    fig.add_trace(go.Bar(name="Isp (vacuum)", x=selected, y=isp_vacs,
                         marker_color=COLORS[0], offsetgroup=0))
    fig.add_trace(go.Bar(name="Isp (sea level)", x=selected, y=isp_sls,
                         marker_color=COLORS[1], offsetgroup=1))
    fig.update_layout(**apply_theme(title="Specific Impulse (seconds)"),
                      barmode="group", height=340, showlegend=True)
    fig.update_yaxes(title_text="Isp (s)")
    st.plotly_chart(fig, use_container_width=True)

    # Propellant data table
    rows = []
    for name in selected:
        p = PROPELLANTS[name]
        rows.append({
            "Propellant":   name,
            "Isp (vac, s)": p["isp_vac"],
            "Isp (SL, s)":  p["isp_sl"],
            "Bulk density (kg/m³)": p["density"],
            "Storable":     "✅" if p["storable"] else "❌ Cryogenic",
            "Toxic":        "⚠️ Yes" if p["toxic"] else "No",
        })
    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.markdown(
        card(
            "📌 <strong>Storable vs Cryogenic:</strong> Storable propellants (solid, N₂O₄/UDMH) "
            "can be kept in tanks at ambient temperature for months or years — enabling quick launch. "
            "Cryogenic propellants (LOX, LH₂) must be loaded shortly before launch, requiring "
            "hours of preparation and large ground support infrastructure. This is why solid-fuel "
            "missiles (Sejjil, Kheibar Shekan) offer faster launch readiness than liquid-fuel systems "
            "(Shahab-3, Ghadr-110).",
            variant="info",
        ),
        unsafe_allow_html=True,
    )


def _rocket_equation_explorer():
    st.markdown(section_header("📐 Rocket Equation Explorer"), unsafe_allow_html=True)
    st.latex(r"\Delta v = I_{sp} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)")

    col1, col2 = st.columns(2)
    with col1:
        isp     = st.slider("Isp (s)", 100, 500, 280)
        m0      = st.slider("Initial mass — m₀ (kg)", 500, 50_000, 10_000, step=500)
        mf      = st.slider("Final (dry) mass — mf (kg)", 100, int(m0*0.95), max(100, int(m0*0.25)), step=100)

    with col2:
        dv      = tsiolkovsky_delta_v(isp, m0, mf)
        pmf     = propellant_mass_fraction(dv, isp)
        prop_kg = m0 - mf
        mr      = m0 / mf

        st.metric("Δv", f"{dv/1000:.3f} km/s  ({dv:.0f} m/s)")
        st.metric("Mass ratio m₀/mf", f"{mr:.2f}")
        st.metric("Propellant mass", f"{prop_kg:,.0f} kg ({prop_kg/m0*100:.0f}% of gross)")

        # Contextual comparison
        contexts = [
            (1.0,  "Low-range SRBM trajectory"),
            (2.5,  "400 km SRBM trajectory (vacuum approx)"),
            (4.0,  "1,000 km MRBM trajectory"),
            (6.0,  "2,000 km MRBM trajectory"),
            (9.4,  "Low Earth Orbit"),
            (11.2, "Earth escape velocity"),
        ]
        for req_kms, label in contexts:
            if dv/1000 >= req_kms:
                st.markdown(f"✅ Sufficient for: {label} (Δv ≥ {req_kms} km/s)")
                break

    # Isp vs mass ratio surface
    st.markdown(sub_header("Δv Surface: Isp × Mass Ratio"), unsafe_allow_html=True)
    import numpy as np
    isps = list(range(200, 501, 20))
    mrs  = [r/10 for r in range(15, 101, 5)]  # 1.5 – 10.0
    Z    = [[tsiolkovsky_delta_v(i, m*1000, 1000)/1000 for m in mrs] for i in isps]

    fig = go.Figure(go.Heatmap(
        x=mrs, y=isps, z=Z,
        colorscale="RdYlGn",
        colorbar=dict(title="Δv (km/s)"),
        hovertemplate="Isp=%{y}s<br>MR=%{x:.1f}<br>Δv=%{z:.2f} km/s<extra></extra>",
    ))
    fig.update_layout(**apply_theme(title="Δv (km/s) — Isp vs Mass Ratio"), height=340)
    fig.update_xaxes(title_text="Mass Ratio (m₀/mf)")
    fig.update_yaxes(title_text="Isp (seconds)")
    st.plotly_chart(fig, use_container_width=True)


def _staging_optimiser():
    st.markdown(section_header("🔢 Multi-Stage Analysis"), unsafe_allow_html=True)
    st.markdown(
        "Staging improves delta-V by discarding spent structure. "
        "Each stage's contribution is computed using the Tsiolkovsky equation applied "
        "sequentially. Reference: Sutton & Biblarz Ch. 4."
    )

    payload = st.number_input("Payload mass (kg)", 100, 5000, 500, step=50)
    n_stages = st.radio("Number of stages", [1, 2, 3], horizontal=True)

    stages = []
    cols = st.columns(n_stages)
    propellant_options = list(PROPELLANTS.keys())

    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Stage {i+1} ({'Boost' if i==0 else 'Upper' if i==1 else 'Final'})**")
            prop = st.selectbox("Propellant", propellant_options,
                                index=i % len(propellant_options), key=f"s_prop_{i}")
            isp_v   = PROPELLANTS[prop]["isp_vac"]
            m_total = st.number_input("Stage gross mass (kg)", 500, 50000, [15000,8000,3000][i], step=500, key=f"s_mt_{i}")
            m_dry   = st.number_input("Stage dry mass (kg)", 100, int(m_total*0.5), max(100, int(m_total*0.08)), step=100, key=f"s_md_{i}")
            thrust  = st.number_input("Thrust (kN)", 10, 5000, [500,200,80][i], step=10, key=f"s_t_{i}")
            stages.append(Stage(
                name=f"Stage {i+1} ({prop})",
                isp_s=isp_v,
                mass_total_kg=m_total,
                mass_structure_kg=m_dry,
                thrust_kn=thrust,
            ))

    result = staging_analysis(stages, payload)

    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Δv", f"{result['total_delta_v_kms']:.2f} km/s")
    col2.metric("Gross mass", f"{result['gross_mass_kg']:,.0f} kg")
    col3.metric("Payload fraction", f"{payload/result['gross_mass_kg']*100:.1f}%")

    # Stage breakdown bar chart
    stage_names = [s["stage"] for s in result["stages"]]
    dvs = [s["delta_v_ms"]/1000 for s in result["stages"]]

    fig = go.Figure(go.Bar(
        x=stage_names, y=dvs,
        marker_color=COLORS[:len(stage_names)],
        text=[f"{d:.2f} km/s" for d in dvs],
        textposition="auto",
    ))
    fig.update_layout(**apply_theme(title="Delta-V by Stage"), height=280, showlegend=False)
    fig.update_yaxes(title_text="Delta-V (km/s)")
    st.plotly_chart(fig, use_container_width=True)

    # Stage table
    import pandas as pd
    rows = []
    for s in result["stages"]:
        rows.append({
            "Stage":          s["stage"],
            "Isp (s)":        f"{s['isp_s']:.0f}",
            "Thrust (kN)":    f"{s['thrust_kn']:.0f}",
            "Burn time (s)":  f"{s['burn_time_s']:.0f}",
            "Mass fraction":  f"{s['mass_fraction']*100:.0f}%",
            "Δv (km/s)":      f"{s['delta_v_ms']/1000:.2f}",
            "Cumulative Δv":  f"{s['cumulative_dv_ms']/1000:.2f} km/s",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def _isp_altitude():
    st.markdown(section_header("📊 Isp vs Altitude"), unsafe_allow_html=True)
    st.markdown(
        "Specific impulse increases with altitude because ambient pressure decreases, "
        "reducing the pressure-thrust penalty on the nozzle exit plane. "
        "A sea-level optimised nozzle underexpands at altitude; a vacuum nozzle "
        "overexpands at sea level."
    )

    selected_props = st.multiselect(
        "Propellants",
        list(PROPELLANTS.keys()),
        default=["Solid (AP/HTPB)", "UDMH / N₂O₄", "LOX / RP-1"],
    )

    fig = go.Figure()
    for i, name in enumerate(selected_props):
        isp_vac = PROPELLANTS[name]["isp_vac"]
        curve   = isp_curve(isp_vac)
        alts    = [c["altitude_km"] for c in curve]
        isps    = [c["isp_s"] for c in curve]
        fig.add_trace(go.Scatter(
            x=alts, y=isps, name=name, mode="lines",
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            hovertemplate=f"{name}<br>Alt: %{{x}} km<br>Isp: %{{y:.0f}} s<extra></extra>",
        ))

    fig.update_layout(**apply_theme(title="Isp vs Altitude"), height=360, showlegend=True)
    fig.update_xaxes(title_text="Altitude (km)")
    fig.update_yaxes(title_text="Specific Impulse (s)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        card(
            "📌 The Isp difference between sea level and vacuum is significant: "
            "a typical solid motor gains ~15 s of Isp from ground to vacuum. "
            "This is why rockets perform better during the high-altitude portion of flight. "
            "Vacuum-optimised nozzles (large exit area ratio) are used on upper stages "
            "that never operate at sea-level pressure.",
            variant="info",
        ),
        unsafe_allow_html=True,
    )


def _reference():
    st.markdown(section_header("📖 Propulsion Reference"), unsafe_allow_html=True)
    st.markdown("""
    ### Key Equations

    **Specific Impulse (Isp)**
    """)
    st.latex(r"I_{sp} = \frac{F}{\dot{m} \cdot g_0} \quad \text{[seconds]}")
    st.markdown("**Thrust**")
    st.latex(r"F = \dot{m} \cdot I_{sp} \cdot g_0 = \dot{m} \cdot v_e + (p_e - p_a) A_e")
    st.markdown("**Characteristic velocity (c*)**")
    st.latex(r"c^* = \frac{p_c A_t}{\dot{m}}")
    st.markdown("**Effective exhaust velocity**")
    st.latex(r"c = I_{sp} \cdot g_0 \quad \text{[m/s]}")
    st.markdown("**Propellant mass flow rate**")
    st.latex(r"\dot{m} = \frac{F}{I_{sp} \cdot g_0}")
    st.markdown("**Burn time from propellant mass**")
    st.latex(r"t_b = \frac{m_{prop}}{\dot{m}}")
    st.markdown("""
    ### Reference
    Sutton, G.P. & Biblarz, O., *Rocket Propulsion Elements*, 9th ed., Wiley, 2017.
    - Chapter 2: Definitions and Fundamentals
    - Chapter 3: Nozzle Theory and Thermodynamic Relations
    - Chapter 4: Flight Performance
    - Chapter 12: Solid Propellant Rocket Fundamentals
    - Chapter 15: Liquid Propellant Rocket Engine Fundamentals
    """)

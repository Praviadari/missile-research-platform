"""
modules/trajectory_simulator.py
================================
Interactive 2D ballistic trajectory simulator.

Physics: Newtonian mechanics + ISA atmosphere + aerodynamic drag.
All equations from Tewari "Atmospheric and Space Flight Dynamics" (2007)
and Anderson "Introduction to Flight" (2015).

Pro-gated page.
"""

import math
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.theme import card, badge, section_header, sub_header, metric_box, plotly_layout, plotly_axis, COLORS
from ui.charts import apply_theme
from utils.physics import BallisticTrajectory, TrajectoryPoint
from utils.units import ms_to_kmh, format_mach, format_range


def render():
    st.title("📈 Trajectory Simulator")
    st.caption(
        "2D ballistic trajectory using RK4 integration with ISA atmosphere and aerodynamic drag. "
        "Equations: Tewari (2007), Anderson (2015). For educational and research use."
    )

    tab_sim, tab_compare, tab_theory = st.tabs([
        "🚀 Single Trajectory", "⚖️ Compare Trajectories", "📐 Theory & Equations"
    ])

    with tab_sim:   _single_trajectory()
    with tab_compare: _compare_trajectories()
    with tab_theory:  _theory()


def _build_trajectory(params: dict) -> tuple:
    sim = BallisticTrajectory(
        launch_angle_deg      = params["angle"],
        burnout_velocity_ms   = params["v0"],
        burnout_altitude_m    = params["h0"] * 1000,
        cd_model              = params["drag"],
        reference_area_m2     = math.pi * (params["radius"]/100)**2,
        dt                    = 1.0,
    )
    pts = sim.simulate(max_time=4000)
    summary = sim.summary(pts)
    return pts, summary


def _single_trajectory():
    st.markdown(section_header("🚀 Single Trajectory"), unsafe_allow_html=True)

    with st.sidebar.expander("⚙️ Trajectory Parameters", expanded=True):
        angle  = st.slider("Launch angle (°)", 10, 85, 45, key="t_angle")
        v0     = st.slider("Burnout velocity (m/s)", 500, 7000, 3000, step=100, key="t_v0")
        h0     = st.slider("Burnout altitude (km)", 5, 150, 80, key="t_h0")
        radius = st.slider("Body radius (cm)", 10, 100, 30, key="t_radius")
        drag   = st.selectbox("Drag model", ["cone", "sphere", "none"], key="t_drag")

    params = dict(angle=angle, v0=v0, h0=h0, radius=radius, drag=drag)
    pts, summary = _build_trajectory(params)

    # ── Summary metrics ───────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Range",        f"{summary.get('range_km',0):.0f} km")
    col2.metric("Apogee",       f"{summary.get('apogee_km',0):.0f} km")
    col3.metric("Flight time",  f"{summary.get('flight_time_s',0)/60:.1f} min")
    col4.metric("Peak Mach",    f"Mach {summary.get('peak_mach',0):.1f}")
    col5.metric("Impact v",     f"{summary.get('impact_velocity_ms',0):.0f} m/s")

    # ── Trajectory plot ───────────────────────────────────────────────────────
    xs   = [p.range_km  for p in pts]
    ys   = [p.altitude_km for p in pts]
    machs= [p.mach for p in pts]
    vs   = [p.v    for p in pts]

    fig = make_subplots(rows=2, cols=2,
        subplot_titles=("Altitude vs Downrange", "Velocity vs Time",
                        "Mach Number vs Altitude", "Dynamic Pressure vs Time"),
        vertical_spacing=0.15, horizontal_spacing=0.12)

    ts = [p.t for p in pts]

    # 1: Trajectory arc
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines",
        line=dict(color=COLORS[0], width=2),
        fill="tozeroy", fillcolor="rgba(231,76,60,0.07)",
        name="Altitude",
        hovertemplate="Range: %{x:.1f} km<br>Alt: %{y:.1f} km<extra></extra>",
    ), row=1, col=1)

    # 2: Velocity vs time
    fig.add_trace(go.Scatter(
        x=ts, y=[p.v/1000 for p in pts], mode="lines",
        line=dict(color=COLORS[1], width=2), name="Velocity (km/s)",
        hovertemplate="t=%{x:.0f}s<br>v=%{y:.2f} km/s<extra></extra>",
    ), row=1, col=2)

    # 3: Mach vs altitude
    fig.add_trace(go.Scatter(
        x=machs, y=ys, mode="lines",
        line=dict(color=COLORS[4], width=2), name="Mach",
        hovertemplate="Mach %{x:.1f}<br>Alt: %{y:.1f} km<extra></extra>",
    ), row=2, col=1)
    # Regime annotations
    for mach_val, label, color in [(1, "Sonic", COLORS[2]), (5, "Hypersonic", COLORS[3])]:
        fig.add_vline(x=mach_val, line_dash="dot", line_color=color,
                      annotation_text=label, annotation_font_size=9, row=2, col=1)

    # 4: Dynamic pressure vs time
    qvals = [p.dynamic_pressure_pa / 1000 for p in pts]  # kPa
    fig.add_trace(go.Scatter(
        x=ts, y=qvals, mode="lines",
        line=dict(color=COLORS[5], width=2), name="Dyn. pressure (kPa)",
        hovertemplate="t=%{x:.0f}s<br>q=%{y:.1f} kPa<extra></extra>",
    ), row=2, col=2)

    fig.update_layout(**plotly_layout(height=560, showlegend=False))
    fig.update_xaxes(title_text="Downrange (km)", row=1, col=1, **_axis())
    fig.update_yaxes(title_text="Altitude (km)",   row=1, col=1, **_axis())
    fig.update_xaxes(title_text="Time (s)",        row=1, col=2, **_axis())
    fig.update_yaxes(title_text="Velocity (km/s)", row=1, col=2, **_axis())
    fig.update_xaxes(title_text="Mach Number",     row=2, col=1, **_axis())
    fig.update_yaxes(title_text="Altitude (km)",   row=2, col=1, **_axis())
    fig.update_xaxes(title_text="Time (s)",        row=2, col=2, **_axis())
    fig.update_yaxes(title_text="Dyn. Pressure (kPa)", row=2, col=2, **_axis())

    st.plotly_chart(fig, use_container_width=True)

    # ── MTCR classification ───────────────────────────────────────────────────
    range_km = summary.get("range_km", 0)
    st.markdown(sub_header("📦 MTCR Classification"), unsafe_allow_html=True)
    if range_km >= 300:
        st.markdown(
            card(f"🔴 This trajectory achieves {range_km:.0f} km range, which meets or exceeds the MTCR Category I "
                 f"300 km range threshold. Combined with payload ≥500 kg, Category I controls would apply.",
                 variant="danger"),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            card(f"🟢 Range {range_km:.0f} km is below the 300 km MTCR threshold.", variant="success"),
            unsafe_allow_html=True,
        )


def _compare_trajectories():
    st.markdown(section_header("⚖️ Compare Multiple Trajectories"), unsafe_allow_html=True)
    st.markdown("Add up to 4 trajectories to compare range, apogee, and flight time side by side.")

    n = st.number_input("Number of trajectories", 2, 4, 2)
    configs = []

    cols = st.columns(n)
    for i, col in enumerate(cols[:n]):
        with col:
            st.markdown(f"**Trajectory {i+1}**")
            configs.append({
                "label":  st.text_input("Label", f"Config {i+1}", key=f"c_label_{i}"),
                "angle":  st.slider("Angle (°)", 10, 85, [35,45,55,65][i%4], key=f"c_ang_{i}"),
                "v0":     st.slider("Burnout v (m/s)", 500, 7000, [2000,3000,4000,5000][i%4], step=200, key=f"c_v0_{i}"),
                "h0":     st.slider("Burnout alt (km)", 5, 150, 80, key=f"c_h0_{i}"),
                "radius": 30,
                "drag":   "cone",
            })

    all_pts, all_summaries = [], []
    for cfg in configs[:n]:
        pts, summary = _build_trajectory(cfg)
        all_pts.append(pts)
        all_summaries.append(summary)

    # Trajectory comparison plot
    fig = go.Figure()
    for i, (pts, cfg) in enumerate(zip(all_pts, configs[:n])):
        fig.add_trace(go.Scatter(
            x=[p.range_km for p in pts],
            y=[p.altitude_km for p in pts],
            name=cfg["label"], mode="lines",
            line=dict(color=COLORS[i], width=2),
            hovertemplate=f"{cfg['label']}<br>Range: %{{x:.1f}} km<br>Alt: %{{y:.1f}} km<extra></extra>",
        ))

    fig.update_layout(**plotly_layout(height=380, showlegend=True, title="Trajectory Comparison"))
    fig.update_xaxes(title_text="Downrange (km)", **_axis())
    fig.update_yaxes(title_text="Altitude (km)", **_axis())
    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    import pandas as pd
    rows = []
    for cfg, s in zip(configs[:n], all_summaries):
        rows.append({
            "Label":          cfg["label"],
            "Angle (°)":      cfg["angle"],
            "Burnout v (m/s)": cfg["v0"],
            "Range (km)":     f"{s.get('range_km',0):.0f}",
            "Apogee (km)":    f"{s.get('apogee_km',0):.0f}",
            "Flight time (min)": f"{s.get('flight_time_s',0)/60:.1f}",
            "Peak Mach":      f"{s.get('peak_mach',0):.1f}",
            "Impact v (m/s)": f"{s.get('impact_velocity_ms',0):.0f}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def _theory():
    st.markdown(section_header("📐 Theory & Equations"), unsafe_allow_html=True)
    st.markdown("""
    ### 2-DOF Point-Mass Equations of Motion

    The simulator integrates Newton's second law for a point mass in a flat-Earth frame:
    """)
    st.latex(r"\ddot{x} = -\frac{1}{2}\rho v^2 C_D A_{ref} \cdot \frac{\dot{x}}{v}")
    st.latex(r"\ddot{y} = -\frac{1}{2}\rho v^2 C_D A_{ref} \cdot \frac{\dot{y}}{v} - g_0")

    st.markdown("""
    where:
    - ρ(h) = ISA air density at altitude h (kg/m³)
    - v = total velocity magnitude (m/s)
    - C_D = drag coefficient (Mach-dependent)
    - A_ref = reference area (m²)
    - g₀ = 9.80665 m/s²

    ### RK4 Integration Scheme
    The state vector **s** = (x, y, ẋ, ẏ) is advanced using 4th-order Runge-Kutta:
    """)
    st.latex(r"\mathbf{s}_{n+1} = \mathbf{s}_n + \frac{\Delta t}{6}(k_1 + 2k_2 + 2k_3 + k_4)")

    st.markdown("""
    ### Cone-Cylinder Drag Model
    For a missile-shaped body (DATCOM empirical correlations):
    """)
    st.latex(r"C_D = C_{D,wave} + C_{D,friction} + C_{D,base}")
    st.latex(r"C_{D,wave} = 2\sin^2\theta \quad (M > 1.5, \text{ Newtonian})")

    st.markdown("""
    ### ISA Atmosphere
    - **Troposphere (0–11 km):** T = 288.15 − 6.5·h K, ρ = ρ₀(T/T₀)^4.256
    - **Stratosphere (11–20 km):** T = 216.65 K (isothermal), ρ decays exponentially

    ### Key References
    - Tewari, A., *Atmospheric and Space Flight Dynamics*, Birkhauser 2007, Ch. 4
    - Anderson, J.D., *Introduction to Flight*, 8th ed., McGraw-Hill 2015, Ch. 9
    - ICAO Doc 7488 / ISO 2533:1975, *International Standard Atmosphere*
    """)


def _axis():
    return dict(gridcolor="#1E2235", zeroline=False, linecolor="#1E2235",
                tickfont={"size":10}, title_font={"size":11})

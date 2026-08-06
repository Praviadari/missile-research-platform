"""
modules/design_lab.py
======================
7-step guided missile research design workflow.

A structured research wizard for academic and policy research:
  1. Mission requirements (range, payload, speed)
  2. Propulsion selection (solid/liquid/hybrid)
  3. Staging architecture
  4. Airframe & aerodynamics
  5. Guidance & navigation concepts
  6. Performance summary & trade-offs
  7. Research bibliography export

This is a research tool — not an operational design tool.
All propulsion / mass / performance estimates are theoretical
from open textbooks and cannot produce a validated flight-ready design.

Pro-gated page.
"""

import math
import streamlit as st
import plotly.graph_objects as go

from ui.theme import card, section_header, sub_header, badge
from ui.charts import apply_theme, COLORS
from utils.physics import Stage, staging_analysis, BallisticTrajectory
from utils.units import tsiolkovsky_delta_v, G0


PROPELLANTS = {
    "Solid (AP/HTPB)":  {"isp_vac": 280, "density": 1750, "storable": True,  "icon": "🟠"},
    "UDMH / N₂O₄":     {"isp_vac": 315, "density": 1200, "storable": True,  "icon": "🟡"},
    "LOX / RP-1":       {"isp_vac": 340, "density": 1030, "storable": False, "icon": "🔵"},
    "LOX / LH₂":        {"isp_vac": 450, "density":  360, "storable": False, "icon": "⚪"},
}

GUIDANCE_CONCEPTS = {
    "Inertial Navigation (INS)":         "Accelerometers + gyroscopes. No external signals. Drift accumulates over time. CEP ~100–300 m.",
    "GPS/GNSS":                          "Very accurate (<10 m CEP) but jammable and spoofable. Often combined with INS.",
    "INS + GPS hybrid":                  "INS for jamming resistance; GPS corrects drift during flight. CEP ~5–30 m.",
    "Terminal radar seeker":             "Active radar illuminates target in terminal phase. All-weather. CEP ~2–10 m.",
    "Terminal EO/IR seeker":             "Electro-optical/infrared camera. Very accurate but weather-limited. CEP ~1–5 m.",
    "Terrain contour matching (TERCOM)": "Matches terrain profile to stored map. Used by cruise missiles. CEP ~30–90 m.",
    "Stellar inertial":                  "Star tracker corrects INS errors mid-flight. Very accurate. CEP ~50–150 m.",
}

AIRFRAME_SHAPES = {
    "Cone-cylinder":     {"cd": 0.25, "L_D": 8,  "notes": "Classic ballistic RV shape. Low drag, simple manufacture."},
    "Ogive-cylinder":    {"cd": 0.22, "L_D": 10, "notes": "Reduced wave drag. Common on anti-ship and cruise missiles."},
    "Blunt body":        {"cd": 0.47, "L_D": 3,  "notes": "High drag — used for reentry vehicles requiring deceleration."},
    "Lifting body":      {"cd": 0.20, "L_D": 12, "notes": "Generates lift for range extension. More complex TPS required."},
    "Waverider":         {"cd": 0.15, "L_D": 8,  "notes": "Uses shock wave for lift. Optimal for Mach 5+. Complex geometry."},
}


def render():
    st.title("🛠️ Design Lab")
    st.caption(
        "7-step structured research workflow. "
        "Generates a parametric research summary — not a validated flight design. "
        "For academic and policy analysis only."
    )

    # Session state for multi-step wizard
    if "dl_step" not in st.session_state:
        st.session_state["dl_step"] = 1
    if "dl_config" not in st.session_state:
        st.session_state["dl_config"] = {}

    STEPS = [
        "1️⃣ Mission Requirements",
        "2️⃣ Propulsion",
        "3️⃣ Staging",
        "4️⃣ Airframe",
        "5️⃣ Guidance",
        "6️⃣ Performance Summary",
        "7️⃣ Research Export",
    ]

    # Progress bar
    step = st.session_state["dl_step"]
    st.progress((step - 1) / (len(STEPS) - 1), text=STEPS[step - 1])
    st.divider()

    # Step dispatch
    if   step == 1: _step_requirements()
    elif step == 2: _step_propulsion()
    elif step == 3: _step_staging()
    elif step == 4: _step_airframe()
    elif step == 5: _step_guidance()
    elif step == 6: _step_performance()
    elif step == 7: _step_export()

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if step > 1 and st.button("← Back"):
            st.session_state["dl_step"] -= 1
            st.rerun()
    with col3:
        if step < len(STEPS) and st.button("Next →", type="primary"):
            st.session_state["dl_step"] += 1
            st.rerun()


def _step_requirements():
    st.markdown(section_header("1️⃣ Mission Requirements"), unsafe_allow_html=True)
    st.markdown("Define the research scenario parameters — range, payload, and speed regime.")

    cfg = st.session_state["dl_config"]

    col1, col2 = st.columns(2)
    with col1:
        cfg["name"]         = st.text_input("Research scenario name", cfg.get("name", "Research Scenario A"))
        cfg["range_km"]     = st.slider("Required range (km)", 100, 5000, cfg.get("range_km", 1000))
        cfg["payload_kg"]   = st.slider("Payload mass (kg)", 100, 2000, cfg.get("payload_kg", 500))
    with col2:
        cfg["target_mach"]  = st.slider("Target peak Mach", 3.0, 25.0, cfg.get("target_mach", 8.0), step=0.5)
        cfg["mission_type"] = st.selectbox("Mission type",
            ["Research / Academic", "Treaty analysis", "Defense policy study"],
            index=["Research / Academic","Treaty analysis","Defense policy study"].index(
                cfg.get("mission_type","Research / Academic")) if cfg.get("mission_type") else 0
        )
        cfg["notes"]        = st.text_area("Research notes", cfg.get("notes", ""), height=80)

    st.session_state["dl_config"] = cfg

    # MTCR flag
    if cfg["range_km"] >= 300 and cfg["payload_kg"] >= 500:
        st.markdown(
            card("⚠️ Parameters meet or exceed MTCR Category I thresholds (≥300 km, ≥500 kg payload). "
                 "Category I systems are subject to a strong presumption of denial under MTCR guidelines.",
                 variant="warning"),
            unsafe_allow_html=True,
        )

    # Delta-V requirement estimate
    dv_req = _estimate_required_dv(cfg["range_km"])
    st.metric("Estimated ΔV required", f"~{dv_req/1000:.1f} km/s",
              help="Rough vacuum delta-V. Actual value depends on trajectory and drag.")


def _step_propulsion():
    st.markdown(section_header("2️⃣ Propulsion Selection"), unsafe_allow_html=True)
    cfg = st.session_state["dl_config"]

    col1, col2 = st.columns(2)
    with col1:
        cfg["propellant"] = st.selectbox("Propellant combination",
            list(PROPELLANTS.keys()),
            index=list(PROPELLANTS.keys()).index(cfg.get("propellant","Solid (AP/HTPB)"))
            if cfg.get("propellant") in PROPELLANTS else 0
        )
        prop = PROPELLANTS[cfg["propellant"]]
        cfg["isp_vac"] = prop["isp_vac"]

        st.metric("Vacuum Isp", f"{prop['isp_vac']} s")
        st.metric("Propellant density", f"{prop['density']} kg/m³")
        st.metric("Storable", "✅ Yes" if prop["storable"] else "❌ Cryogenic")

    with col2:
        st.markdown(sub_header("Trade-off summary"), unsafe_allow_html=True)
        comparisons = []
        for name, p in PROPELLANTS.items():
            dv = tsiolkovsky_delta_v(p["isp_vac"], 10000, 2000)
            comparisons.append((name, p["isp_vac"], dv/1000, p["storable"]))

        fig = go.Figure(go.Bar(
            y=[c[0].split("(")[0][:20] for c in comparisons],
            x=[c[1] for c in comparisons],
            orientation="h",
            marker_color=[COLORS[0] if c[0]==cfg["propellant"] else "#1E2235" for c in comparisons],
        ))
        fig.update_layout(**apply_theme(height=200), showlegend=False, margin=dict(l=10,r=10,t=10,b=10))
        fig.update_xaxes(title_text="Isp (s)", gridcolor="#1E2235", zeroline=False)
        st.plotly_chart(fig, use_container_width=True)

    st.session_state["dl_config"] = cfg


def _step_staging():
    st.markdown(section_header("3️⃣ Staging Architecture"), unsafe_allow_html=True)
    cfg = st.session_state["dl_config"]

    dv_req = _estimate_required_dv(cfg.get("range_km", 1000))
    isp    = cfg.get("isp_vac", 280)

    cfg["n_stages"] = st.radio("Number of stages", [1, 2, 3], horizontal=True,
                                index=[1,2,3].index(cfg.get("n_stages",2)) - 1)

    stages = []
    cols = st.columns(cfg["n_stages"])
    stage_configs = cfg.get("stage_configs", [{} for _ in range(3)])

    for i, col in enumerate(cols[:cfg["n_stages"]]):
        with col:
            st.markdown(f"**Stage {i+1}**")
            sc = stage_configs[i] if i < len(stage_configs) else {}
            m_gross = st.number_input("Gross mass (kg)", 500, 50000,
                                      sc.get("m_gross",[15000,8000,3000][i%3]), step=500, key=f"dl_mg_{i}")
            m_dry   = st.number_input("Dry mass (kg)", 100, int(m_gross*0.5),
                                      min(int(m_gross*0.08), sc.get("m_dry",[1200,640,240][i%3])),
                                      step=100, key=f"dl_md_{i}")
            thrust  = st.number_input("Thrust (kN)", 10, 5000, sc.get("thrust",[600,250,100][i%3]),
                                      step=10, key=f"dl_thr_{i}")
            stages.append(Stage(f"Stage {i+1}", isp, m_gross, m_dry, thrust))
            stage_configs[i] = {"m_gross": m_gross, "m_dry": m_dry, "thrust": thrust}

    cfg["stage_configs"] = stage_configs
    payload = cfg.get("payload_kg", 500)
    result  = staging_analysis(stages, payload)
    cfg["staging_result"] = result

    col1, col2, col3 = st.columns(3)
    dv_total = result["total_delta_v_kms"]
    col1.metric("Total ΔV", f"{dv_total:.2f} km/s",
                delta=f"{'✅' if dv_total >= dv_req/1000 else '❌'} Need {dv_req/1000:.1f} km/s")
    col2.metric("Gross mass", f"{result['gross_mass_kg']:,.0f} kg")
    col3.metric("Payload fraction", f"{payload/result['gross_mass_kg']*100:.1f}%")

    st.session_state["dl_config"] = cfg


def _step_airframe():
    st.markdown(section_header("4️⃣ Airframe & Aerodynamics"), unsafe_allow_html=True)
    cfg = st.session_state["dl_config"]

    cfg["airframe"] = st.selectbox("Nose/body shape",
        list(AIRFRAME_SHAPES.keys()),
        index=list(AIRFRAME_SHAPES.keys()).index(cfg.get("airframe","Cone-cylinder"))
        if cfg.get("airframe") in AIRFRAME_SHAPES else 0
    )
    shape = AIRFRAME_SHAPES[cfg["airframe"]]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Reference Cd", f"{shape['cd']:.2f}")
        st.metric("L/D ratio", f"{shape['L_D']}")
        cfg["body_radius_m"] = st.slider("Body radius (m)", 0.1, 1.5, cfg.get("body_radius_m", 0.3), step=0.05)
    with col2:
        st.markdown(card(f"📐 <strong>{cfg['airframe']}</strong><br>{shape['notes']}", variant="info"),
                    unsafe_allow_html=True)

    cfg["ref_area_m2"] = math.pi * cfg["body_radius_m"] ** 2
    st.caption(f"Reference area: {cfg['ref_area_m2']:.3f} m²")
    st.session_state["dl_config"] = cfg


def _step_guidance():
    st.markdown(section_header("5️⃣ Guidance & Navigation"), unsafe_allow_html=True)
    cfg = st.session_state["dl_config"]

    cfg["guidance"] = st.selectbox("Primary guidance concept",
        list(GUIDANCE_CONCEPTS.keys()),
        index=list(GUIDANCE_CONCEPTS.keys()).index(cfg.get("guidance","INS + GPS hybrid"))
        if cfg.get("guidance") in GUIDANCE_CONCEPTS else 2
    )
    cfg["guidance_backup"] = st.selectbox("Backup / terminal guidance",
        ["None"] + list(GUIDANCE_CONCEPTS.keys()),
        index=0
    )

    for name, desc in GUIDANCE_CONCEPTS.items():
        marker = "✅" if name == cfg["guidance"] else ("🔸" if name == cfg.get("guidance_backup") else "  ")
        st.markdown(f"{marker} **{name}** — {desc}")

    st.session_state["dl_config"] = cfg


def _step_performance():
    st.markdown(section_header("6️⃣ Performance Summary"), unsafe_allow_html=True)
    cfg = st.session_state["dl_config"]

    # Run trajectory
    isp  = cfg.get("isp_vac", 280)
    sr   = cfg.get("staging_result", {})
    dv   = sr.get("total_delta_v_ms", 3500) if sr else 3500
    v0   = min(dv * 0.85, 7000)  # approximate burnout velocity

    sim = BallisticTrajectory(
        launch_angle_deg=45, burnout_velocity_ms=v0,
        burnout_altitude_m=80_000, cd_model="cone",
        reference_area_m2=cfg.get("ref_area_m2", 0.28), dt=5.0,
    )
    pts     = sim.simulate(max_time=5000)
    summary = sim.summary(pts)

    st.markdown(f"### {cfg.get('name','Research Scenario')}")

    # Metrics
    metrics = [
        ("Estimated Range",  f"{summary.get('range_km',0):.0f} km",    f"Target: {cfg.get('range_km',0)} km"),
        ("Apogee",           f"{summary.get('apogee_km',0):.0f} km",    None),
        ("Flight Time",      f"{summary.get('flight_time_s',0)/60:.1f} min", None),
        ("Peak Mach",        f"Mach {summary.get('peak_mach',0):.1f}",  f"Target: Mach {cfg.get('target_mach',0):.0f}"),
        ("Impact velocity",  f"{summary.get('impact_velocity_ms',0):.0f} m/s", None),
        ("Total ΔV",         f"{sr.get('total_delta_v_kms',0):.2f} km/s" if sr else "N/A", None),
    ]
    cols = st.columns(3)
    for i, (label, val, delta) in enumerate(metrics):
        cols[i % 3].metric(label, val, delta=delta)

    # Trajectory plot
    fig = go.Figure(go.Scatter(
        x=[p.range_km for p in pts], y=[p.altitude_km for p in pts],
        mode="lines", fill="tozeroy",
        fillcolor="rgba(231,76,60,0.08)",
        line=dict(color=COLORS[0], width=2),
    ))
    fig.update_layout(**apply_theme(title="Estimated Trajectory"), height=300, showlegend=False)
    fig.update_xaxes(title_text="Downrange (km)", gridcolor="#1E2235", zeroline=False)
    fig.update_yaxes(title_text="Altitude (km)", gridcolor="#1E2235", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

    cfg["summary"] = summary
    st.session_state["dl_config"] = cfg


def _step_export():
    st.markdown(section_header("7️⃣ Research Export"), unsafe_allow_html=True)
    cfg = st.session_state["dl_config"]
    sr  = cfg.get("staging_result", {})
    sm  = cfg.get("summary", {})

    report = f"""# Research Scenario: {cfg.get('name','Unnamed')}
**Mission type:** {cfg.get('mission_type','')}
**Generated by:** Missile Analysis & Research Platform v2

---

## Mission Requirements
| Parameter | Value |
|-----------|-------|
| Range | {cfg.get('range_km','')} km |
| Payload | {cfg.get('payload_kg','')} kg |
| Target Mach | {cfg.get('target_mach','')} |

## Propulsion
| Parameter | Value |
|-----------|-------|
| Propellant | {cfg.get('propellant','')} |
| Isp (vacuum) | {cfg.get('isp_vac','')} s |
| Stages | {cfg.get('n_stages','')} |
| Total ΔV | {sr.get('total_delta_v_kms','N/A')} km/s |
| Gross mass | {sr.get('gross_mass_kg','N/A'):,} kg |

## Airframe
| Parameter | Value |
|-----------|-------|
| Shape | {cfg.get('airframe','')} |
| Body radius | {cfg.get('body_radius_m','')} m |
| Reference area | {cfg.get('ref_area_m2',0):.3f} m² |

## Guidance
- **Primary:** {cfg.get('guidance','')}
- **Backup/terminal:** {cfg.get('guidance_backup','None')}

## Performance (Theoretical)
| Parameter | Value |
|-----------|-------|
| Estimated range | {sm.get('range_km',0):.0f} km |
| Apogee | {sm.get('apogee_km',0):.0f} km |
| Flight time | {sm.get('flight_time_s',0)/60:.1f} min |
| Peak Mach | {sm.get('peak_mach',0):.1f} |

## Notes
{cfg.get('notes','')}

## Research References
- Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., Wiley, 2017
- Tewari, *Atmospheric and Space Flight Dynamics*, Birkhauser, 2007
- Anderson, *Introduction to Flight*, 8th ed., McGraw-Hill, 2015
- CSIS Missile Defense Project: https://missilethreat.csis.org
- IISS Military Balance 2023

---
*This summary is a parametric research estimate only. It does not constitute
a validated flight design and cannot be used for operational purposes.*
"""

    st.text_area("Research Summary (Markdown)", report, height=400)
    st.download_button(
        "📥 Download Research Summary",
        data=report,
        file_name=f"research_{cfg.get('name','scenario').replace(' ','_').lower()}.md",
        mime="text/markdown",
    )

    if st.button("🔄 Start New Scenario"):
        st.session_state["dl_step"] = 1
        st.session_state["dl_config"] = {}
        st.rerun()


def _estimate_required_dv(range_km: float) -> float:
    """Rough ΔV estimate from range, using simplified vacuum ballistic equations."""
    g   = G0
    R   = 6_371_000.0
    phi = (range_km * 1000) / (2 * R)
    v   = math.sqrt(g * R * math.tan(phi)) if phi < math.pi/4 else math.sqrt(g * R)
    return min(v, 7800.0)

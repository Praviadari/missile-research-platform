"""
modules/learning_center.py
============================
Interactive educational modules covering missile physics concepts.

Tabs:
  1. Ballistic Physics         — atmosphere, gravity, trajectory concepts
  2. Rocket Propulsion         — Isp, rocket equation, staging
  3. Guidance & Accuracy       — CEP, guidance types, error sources
  4. Missile Defense Concepts  — layered defense, intercept challenges
  5. History & Doctrine        — Cold War deterrence, modern doctrine
  6. Learning Path             — curated study progression

All content is educational — interactive sliders illustrate underlying
physics principles. No operational targeting or attack planning features.

Public page — no authentication required.
"""

import math
import streamlit as st

from ui.theme import card, badge, section_header, sub_header
from ui.charts import (
    isp_comparison_chart,
    atmospheric_density_profile,
    rocket_equation_chart,
    apply_theme,
    COLORS,
)


def render():
    st.title("🎓 Missile Systems — Learning Center")
    st.caption(
        "Interactive physics education modules. "
        "Concepts illustrated with sliders and worked examples. "
        "All equations from standard aerospace engineering references."
    )

    tabs = st.tabs([
        "🌍 Ballistic Physics",
        "🔥 Rocket Propulsion",
        "🎯 Guidance & Accuracy",
        "🛡️ Defense Concepts",
        "📅 History & Doctrine",
        "🗺️ Learning Path",
    ])

    with tabs[0]: _ballistic_physics()
    with tabs[1]: _propulsion()
    with tabs[2]: _guidance()
    with tabs[3]: _defense_concepts()
    with tabs[4]: _history_doctrine()
    with tabs[5]: _learning_path()


# ── Tab 1: Ballistic Physics ──────────────────────────────────────────────────

def _ballistic_physics():
    st.markdown(section_header("🌍 Ballistic Physics"), unsafe_allow_html=True)
    st.markdown(
        "Ballistic missiles follow trajectories governed by classical mechanics: "
        "initial velocity, gravity, and atmospheric drag. Understanding these "
        "principles is foundational to analyzing missile performance."
    )

    tab_atm, tab_grav, tab_traj = st.tabs([
        "🌫️ Atmosphere", "🌐 Gravity & Range", "📈 Trajectory Concepts"
    ])

    with tab_atm:
        st.markdown(sub_header("International Standard Atmosphere (ISA)"), unsafe_allow_html=True)
        st.markdown(
            "The ISA defines how air density, pressure, and temperature vary with altitude. "
            "This matters for drag calculations — at high altitudes, thin air means almost "
            "no aerodynamic drag, while at sea level drag is significant."
        )
        fig = atmospheric_density_profile()
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Source: ICAO Standard Atmosphere (ISO 2533:1975)")

        st.markdown("""
        **Key ISA layers:**
        - **Troposphere (0–11 km):** Temperature drops 6.5 K/km. Most weather occurs here.
        - **Tropopause (11 km):** Temperature stabilizes at −56.5°C.
        - **Stratosphere (11–50 km):** Temperature slowly rises. Very low drag.
        - **Above 50 km:** Near-vacuum conditions. Ballistic missiles coast here.
        - **Kármán line (~80–100 km):** Conventional boundary of space.
        """)

        st.markdown(sub_header("Interactive: Speed of Sound vs Altitude"), unsafe_allow_html=True)
        alt_km = st.slider("Altitude (km)", 0, 80, 20)
        h_m = alt_km * 1000

        # ISA temperature
        if h_m <= 11000:
            T = 288.15 - 0.0065 * h_m
        elif h_m <= 20000:
            T = 216.65
        else:
            T = 216.65 + 0.001 * (h_m - 20000)

        sos   = math.sqrt(1.4 * 287.05 * max(T, 1))
        rho0  = 1.225
        rho   = rho0 * math.exp(-h_m / 8500) if h_m > 0 else rho0

        col1, col2, col3 = st.columns(3)
        col1.metric("Temperature", f"{T - 273.15:.1f} °C")
        col2.metric("Speed of Sound", f"{sos:.0f} m/s ({sos/340.3:.2f}× sea level)")
        col3.metric("Air Density", f"{rho:.4f} kg/m³ ({rho/1.225*100:.1f}% of sea level)")

        st.markdown(
            card(
                f"At {alt_km} km altitude, air density is <strong>{rho/1.225*100:.1f}%</strong> "
                f"of sea-level density. Aerodynamic drag force is proportional to air density, "
                f"so a missile at this altitude experiences approximately "
                f"<strong>{rho/1.225*100:.1f}%</strong> of its sea-level drag.",
                variant="info",
            ),
            unsafe_allow_html=True,
        )

    with tab_grav:
        st.markdown(sub_header("Gravity and Ballistic Range"), unsafe_allow_html=True)
        st.markdown(
            "In vacuum (no air resistance), a ballistic projectile's range depends only "
            "on initial velocity and launch angle. The classic range equation:"
        )
        st.latex(r"R = \frac{v_0^2 \sin(2\theta)}{g}")
        st.markdown(
            "where R = range, v₀ = initial velocity, θ = launch angle, g = gravitational acceleration. "
            "Maximum range occurs at θ = 45°. Real missiles have different optimal angles "
            "due to drag and Earth's curvature."
        )

        st.markdown(sub_header("Interactive: Vacuum Range Calculator"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            v0_ms = st.slider("Initial velocity (m/s)", 500, 7000, 3000, step=100)
            theta  = st.slider("Launch angle (°)", 10, 80, 45)
        with col2:
            g = 9.80665
            R_vacuum = (v0_ms**2 * math.sin(math.radians(2 * theta))) / g / 1000
            apogee   = (v0_ms * math.sin(math.radians(theta)))**2 / (2 * g) / 1000
            flight_t = 2 * v0_ms * math.sin(math.radians(theta)) / g

            st.metric("Range (vacuum)", f"{R_vacuum:.0f} km")
            st.metric("Apogee (vacuum)", f"{apogee:.0f} km")
            st.metric("Flight time (vacuum)", f"{flight_t:.0f} s ({flight_t/60:.1f} min)")

        st.markdown(
            card(
                "⚠️ <strong>Real-world note:</strong> Actual missile ranges are substantially less "
                "than vacuum calculations due to atmospheric drag, especially at lower altitudes. "
                "For ballistic missiles, actual range is typically 60–80% of the vacuum figure "
                "depending on trajectory shape and altitude profile.",
                variant="warning",
            ),
            unsafe_allow_html=True,
        )

    with tab_traj:
        st.markdown(sub_header("Ballistic Trajectory Phases"), unsafe_allow_html=True)
        st.markdown("""
        A ballistic missile flight has three distinct phases:

        **1. Boost Phase** (30–300 seconds)
        - Rocket motor burns; missile accelerates to burnout velocity
        - Most vulnerable phase for boost-phase intercept (heat signature)
        - Typically 150–300 km altitude at burnout for MRBMs

        **2. Midcourse Phase** (most of flight time)
        - Motor has burned out; missile coasts in a ballistic arc
        - Above atmosphere: minimal drag, predictable trajectory
        - Flight times: SRBM ~5 min, MRBM ~12 min, ICBM ~30 min

        **3. Terminal Phase** (last ~60–120 seconds)
        - Reentry into atmosphere; severe aerodynamic heating
        - Drag decelerates warhead
        - Maneuvering reentry vehicles (MaRV) can alter trajectory here
        - Most theater missile defenses engage in this phase
        """)

        st.markdown(
            card(
                "🎯 <strong>Hypersonic glide vehicles (HGVs)</strong> complicate this picture: "
                "after booster burnout, an HGV glides at high speed within the upper atmosphere "
                "(30–60 km altitude) rather than following a ballistic arc. This eliminates the "
                "predictable midcourse phase and significantly reduces the engagement window "
                "available to missile defenses.",
                variant="info",
            ),
            unsafe_allow_html=True,
        )


# ── Tab 2: Propulsion ─────────────────────────────────────────────────────────

def _propulsion():
    st.markdown(section_header("🔥 Rocket Propulsion"), unsafe_allow_html=True)

    tab_isp, tab_eq, tab_types = st.tabs([
        "📊 Specific Impulse", "📐 Rocket Equation", "⚗️ Propellant Types"
    ])

    with tab_isp:
        st.markdown(sub_header("Specific Impulse (Isp)"), unsafe_allow_html=True)
        st.markdown(
            "Specific impulse is the key measure of propellant efficiency — "
            "how much thrust you get per unit of propellant consumed per second. "
            "Higher Isp means longer range for the same amount of propellant."
        )
        st.latex(r"I_{sp} = \frac{F}{\dot{m} \cdot g_0} \quad \text{(seconds)}")
        st.markdown("where F = thrust (N), ṁ = mass flow rate (kg/s), g₀ = 9.80665 m/s²")

        fig = isp_comparison_chart()
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Source: Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017)")

    with tab_eq:
        st.markdown(sub_header("Tsiolkovsky Rocket Equation"), unsafe_allow_html=True)
        st.markdown(
            "The rocket equation relates delta-V (change in velocity) to propellant efficiency "
            "and mass fraction. It is the fundamental constraint on all rocket performance."
        )
        st.latex(r"\Delta v = I_{sp} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)")
        st.markdown("where m₀ = initial mass (fully fueled), m_f = final mass (empty of propellant)")

        fig = rocket_equation_chart()
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(sub_header("Interactive: Delta-V Calculator"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            isp_s   = st.slider("Isp (seconds)", 150, 500, 280)
            m_ratio = st.slider("Mass ratio (m₀/mf)", 1.5, 10.0, 4.0, step=0.1)
        with col2:
            G0     = 9.80665
            dv_ms  = isp_s * G0 * math.log(m_ratio)
            dv_kms = dv_ms / 1000
            pf     = 1 - 1/m_ratio

            st.metric("Delta-V", f"{dv_kms:.2f} km/s")
            st.metric("Propellant mass fraction", f"{pf*100:.0f}%")

        st.markdown(
            card(
                f"With Isp={isp_s}s and mass ratio={m_ratio:.1f}, this system achieves "
                f"Δv = <strong>{dv_kms:.2f} km/s</strong>. "
                f"{pf*100:.0f}% of launch mass is propellant. "
                "For reference: achieving low Earth orbit requires ~9.4 km/s; "
                "a 2,000 km MRBM trajectory requires approximately 4–5 km/s.",
                variant="info",
            ),
            unsafe_allow_html=True,
        )

    with tab_types:
        st.markdown(sub_header("Propellant Types & Trade-offs"), unsafe_allow_html=True)
        st.markdown(
            card(
                "**Solid propellant** (HTPB/AP composites): Isp ~265–285s. "
                "Advantages: stored ready-to-launch (minutes vs hours), simpler logistics, "
                "smaller ground footprint. Disadvantages: cannot be throttled, "
                "lower Isp than liquid. Used by: Fateh series, Kheibar Shekan, Sejjil, "
                "most US strategic missiles, MTCR-class systems globally.",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            card(
                "**Liquid propellant** (UDMH/N₂O₄, LOX/RP-1): Isp ~285–340s. "
                "Advantages: higher Isp (more range for same mass), throttleable. "
                "Disadvantages: corrosive, toxic, requires fueling before launch (hours), "
                "larger ground support infrastructure, vulnerable during fueling. "
                "Used by: Shahab-3, Ghadr, Qiam-1, older Soviet/Russian systems.",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            card(
                "**Turbofan/Turbojet** (cruise missiles): Isp ~3,000–5,000s (air-breathing!). "
                "Dramatically higher efficiency because engine uses atmospheric oxygen — "
                "no need to carry oxidizer. Range advantage at low altitude. "
                "Disadvantages: limited to subsonic/low-supersonic speeds, "
                "low altitude (radar-detectable). Used by: Tomahawk, Kalibr, Hoveizeh.",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            card(
                "**Scramjet** (hypersonic cruise): Air-breathing at Mach 5–25. "
                "No rotating parts — supersonic combustion. Very high theoretical Isp. "
                "Extremely difficult engineering: inlet must maintain supersonic flow, "
                "combustion residence time < 1 millisecond, severe heating. "
                "Operational examples: claimed for Zircon (Russia), Fattah-2 (Iran — disputed). "
                "Demonstrated in: X-51A Waverider (US, 2013), Chinese experimental vehicles.",
                variant="info",
            ),
            unsafe_allow_html=True,
        )


# ── Tab 3: Guidance & Accuracy ────────────────────────────────────────────────

def _guidance():
    st.markdown(section_header("🎯 Guidance Systems & Accuracy"), unsafe_allow_html=True)
    st.markdown(
        "Guidance determines where a missile hits. Accuracy is measured by "
        "Circular Error Probable (CEP) — the radius within which 50% of warheads "
        "from a given missile type would land."
    )

    st.latex(r"\text{CEP} = \text{radius such that } P(\text{hit within}) = 0.5")

    st.markdown(
        card(
            "📌 <strong>CEP context:</strong> A missile with CEP=30m means half of all shots "
            "land within 30m of the aim point. To reliably destroy a hardened point target "
            "(like a reinforced bunker), CEP typically needs to be less than 30–50m. "
            "For area targets (airfields, fuel depots), CEP of 100–300m may suffice. "
            "Unguided rockets may have CEP of 1,000–5,000m, limiting them to area effects.",
            variant="info",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(sub_header("Guidance Types"), unsafe_allow_html=True)

    guidance_data = [
        ("Inertial Navigation (INS)", "Uses accelerometers/gyroscopes to track position from known starting point. Drift error accumulates over time — typical CEP 500–2,500m at MRBM ranges. No external signal required. Jam-resistant.", "muted"),
        ("GPS/GLONASS/BeiDou + INS", "Satellite navigation corrects INS drift. Provides ~5–50m CEP regardless of range. Vulnerable to GPS jamming/spoofing. Now standard on modern precision-strike missiles.", "info"),
        ("TERCOM (Terrain Contour Matching)", "Cruise missile matches radar altimeter readings to stored terrain map. ~10–30m CEP, jam-resistant, only works over terrain with distinctive topography. Used in Tomahawk.", "success"),
        ("DSMAC (Digital Scene Matching)", "Terminal phase optical match of pre-loaded image to target. ~3–10m CEP. Requires clear visibility; ineffective in smoke, cloud, night without FLIR. Used in Tomahawk Block IV/V.", "success"),
        ("Active Radar Seeker", "Terminal homing on radar return from target. Effective against ships and hardened targets. Used in anti-ship missiles, some modern ballistic warheads. Expensive.", "warning"),
        ("Maneuvering Reentry Vehicle (MaRV)", "Post-burnout steering via control surfaces or thrust vectoring during reentry. Allows in-flight correction, complicates intercept geometry. Used in Kheibar Shekan, DF-21D, Emad.", "danger"),
    ]

    for gtype, desc, var in guidance_data:
        st.markdown(card(f"<strong>{gtype}</strong><br>{desc}", variant=var), unsafe_allow_html=True)

    st.markdown(sub_header("CEP Comparison (Approximate)"), unsafe_allow_html=True)
    import plotly.graph_objects as go
    systems = ["Unguided rocket\n(Qassam)", "Shahab-3\n(INS only)", "Qiam-1\n(INS)", "Ghadr-110\n(INS)", "Emad\n(MaRV)", "Kheibar Shekan\n(MaRV+GPS)", "Tomahawk\n(TERCOM+DSMAC)", "AGM-158B\n(GPS+IIR)"]
    ceps    = [2500, 2500, 500, 800, 500, 50, 5, 3]

    fig = go.Figure(go.Bar(
        x=systems, y=ceps,
        marker=dict(color=[COLORS[0] if c > 500 else COLORS[1] if c > 50 else COLORS[3] for c in ceps]),
        hovertemplate="<b>%{x}</b><br>CEP: ~%{y} m<extra></extra>",
    ))
    fig.add_hline(y=50,  line_dash="dash", line_color=COLORS[3], annotation_text="50m — point target capable")
    fig.add_hline(y=300, line_dash="dot",  line_color=COLORS[1], annotation_text="300m — area target capable")
    fig.update_layout(**apply_theme(title="Approximate CEP by Guidance System"), height=350, showlegend=False)
    fig.update_yaxes(title_text="CEP (metres)", type="log")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Approximate values. Sources: CSIS, IISS, Janes. Classified guidance upgrades may differ.")


# ── Tab 4: Defense Concepts ───────────────────────────────────────────────────

def _defense_concepts():
    st.markdown(section_header("🛡️ Missile Defense Concepts"), unsafe_allow_html=True)

    tab_layers, tab_challenge = st.tabs(["🏛️ Layered Defense", "⚡ Intercept Challenges"])

    with tab_layers:
        st.markdown(sub_header("Layered Missile Defense Architecture"), unsafe_allow_html=True)
        st.markdown("""
        Modern missile defense uses multiple overlapping layers, each designed to intercept
        different threat types at different altitudes and phases of flight. The US/Israeli
        model is the most developed example:

        **Layer 1: Exo-atmospheric (Space)**
        - Systems: Arrow-3, SM-3 Block IIA
        - Altitude: 50–1,000 km
        - Phase: Late midcourse
        - Intercept method: Hit-to-kill kinetic vehicle

        **Layer 2: Upper endo-atmospheric (High altitude)**
        - Systems: THAAD, Arrow-2
        - Altitude: 40–150 km
        - Phase: Terminal / late midcourse
        - Intercept method: Hit-to-kill

        **Layer 3: Lower endo-atmospheric (Medium altitude)**
        - Systems: Patriot PAC-3 MSE, David's Sling
        - Altitude: 1–40 km
        - Phase: Terminal
        - Intercept method: Hit-to-kill or proximity fuze

        **Layer 4: Point defense (Low altitude)**
        - Systems: Iron Dome, Phalanx CIWS, C-RAM
        - Altitude: 0–10 km
        - Threat: Rockets, artillery, mortars, cruise missiles
        - Intercept method: Fragmentation warhead or kinetic
        """)

    with tab_challenge:
        st.markdown(sub_header("Intercept Challenges"), unsafe_allow_html=True)
        st.markdown(
            "Missile defense is extremely difficult engineering. Key challenges include:"
        )
        challenges = [
            ("Closing velocity", "Interceptor must close on target moving at Mach 5–10+. Relative closing speeds can exceed Mach 15, leaving fractions of a second for course corrections."),
            ("Discrimination", "Real warheads must be distinguished from decoys, debris, and submunitions. A MaRV that releases decoys near apogee multiplies this challenge."),
            ("Salvo saturation", "A single interceptor battery has finite simultaneous engagement capacity. Firing a large salvo (e.g., 181 missiles in True Promise II) can exceed this capacity, guaranteeing some penetration."),
            ("Maneuvering reentry vehicles", "Unpredictable terminal maneuvers require interceptors to predict future position. MaRV maneuvers cut available intercept time."),
            ("Hypersonic glide vehicles", "HGVs fly at low altitude and high speed, bypassing exo-atmospheric interceptors entirely and providing limited engagement time for terminal systems."),
            ("Engagement geometry", "Defense systems have a specific engagement envelope (altitude, range, speed). If attacker's trajectory avoids this envelope, the system cannot engage."),
        ]
        for challenge, desc in challenges:
            st.markdown(
                card(f"⚠️ <strong>{challenge}</strong><br>{desc}", variant="plain"),
                unsafe_allow_html=True,
            )


# ── Tab 5: History & Doctrine ─────────────────────────────────────────────────

def _history_doctrine():
    st.markdown(section_header("📅 History & Strategic Doctrine"), unsafe_allow_html=True)

    st.markdown("""
    ### Cold War Origins

    Ballistic missiles emerged from WWII German V-2 technology. The US and USSR rapidly
    developed long-range missiles after the war, leading to the nuclear-armed ICBM arsenals
    that defined Cold War deterrence.

    **Mutual Assured Destruction (MAD):** The doctrine that any nuclear first strike would
    trigger a devastating retaliatory strike, making nuclear war suicidal. This relied on
    second-strike survivability — enough nuclear forces surviving a first strike to destroy
    the attacker. ICBMs in hardened silos, submarine-launched ballistic missiles (SLBMs),
    and bomber aircraft formed the US "nuclear triad."

    ### Conventional Precision Strike Revolution

    The Gulf War (1991) demonstrated precision conventional missiles at scale for the first
    time — Tomahawk cruise missiles struck Baghdad command infrastructure with ~10m accuracy.
    This "Revolution in Military Affairs" transformed warfare: precision-guided munitions
    allowed striking specific buildings within city blocks.

    ### Regional Ballistic Missile Proliferation

    The 1990s–2000s saw ballistic missile technology spread beyond the superpowers.
    Countries including Iran, North Korea, Pakistan, India, and others developed indigenous
    programs — often based on Soviet Scud technology — for regional deterrence and power
    projection. The MTCR attempted to slow this but had limited success.

    ### Modern Hypersonic Competition

    The 2010s–2020s saw the US, Russia, and China invest heavily in hypersonic systems.
    Russia claimed operational Kinzhal and Avangard deployments. China demonstrated DF-ZF.
    The US has faced development delays (ARRW program cancellation for USAF, Army LRHW
    continues). These systems exploit a gap between existing air defense layers.

    ### Doctrine in Practice: Iran

    Iran's missile doctrine serves multiple purposes:
    - **Deterrence:** Large missile arsenal threatens regional adversaries with retaliation
    - **Escalation management:** True Promise I & II calibrated to demonstrate capability
      without triggering broader war
    - **Proxy empowerment:** Missile technology transferred to Hezbollah, Houthis, Iraqi
      militias extends influence without direct attribution
    - **Asymmetric offset:** Counters Israeli/US air superiority with long-range strike
    """)


# ── Tab 6: Learning Path ──────────────────────────────────────────────────────

def _learning_path():
    st.markdown(section_header("🗺️ Recommended Learning Path"), unsafe_allow_html=True)
    st.markdown("A structured progression from beginner to advanced in missile technology and policy.")

    levels = [
        ("🟢 Beginner", [
            ("CSIS Missile Defense Project website", "missilethreat.csis.org — start here for specifications and basic concepts"),
            ("Arms Control Association Fact Sheets", "armscontrol.org/factsheets — clear policy summaries"),
            ("NTI Country Profiles", "nti.org/countries — who has what capabilities"),
            ("This Learning Center", "Work through all tabs above in order"),
        ]),
        ("🟡 Intermediate", [
            ("IISS Military Balance", "Annual reference — find it in your library. Read the missile forces sections"),
            ("Arms Control Wonk podcast/blog", "Expert analysis of current developments"),
            ("38 North", "Specialized DPRK analysis using open-source satellite imagery"),
            ("Janes Defence Intelligence", "Professional database — available via many university libraries"),
        ]),
        ("🔴 Advanced", [
            ("Sutton & Biblarz: Rocket Propulsion Elements", "The definitive propulsion textbook. Focus on Chapters 2, 3, 12, 15"),
            ("Tewari: Atmospheric and Space Flight Dynamics", "Rigorous treatment of ballistic trajectories"),
            ("Nonproliferation Review (journal)", "Peer-reviewed policy research"),
            ("DoD Annual Reports (China, Russia)", "Declassified US government assessments"),
            ("RAND Corporation studies on missile defense", "Quantitative policy analysis"),
        ]),
    ]

    for level, resources in levels:
        with st.expander(f"**{level}**", expanded=level == "🟢 Beginner"):
            for title, desc in resources:
                st.markdown(f"**{title}**")
                st.markdown(f"  _{desc}_")
                st.markdown("")

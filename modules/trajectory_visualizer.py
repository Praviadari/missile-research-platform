"""
modules/trajectory_visualizer.py
==================================
3D trajectory visualizer using Plotly 3D scatter/line plots.

Shows missile arcs on a simplified spherical Earth surface,
with altitude exaggeration for clarity.

Pro-gated page.
"""

import math
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from ui.theme import card, section_header, badge
from ui.charts import apply_theme, COLORS
from utils.physics import BallisticTrajectory, TrajectoryPoint
from utils.units import haversine_range


def render():
    st.title("🌐 3D Trajectory Visualizer")
    st.caption("Three-dimensional trajectory and multi-launch visualization on a globe projection.")

    tabs = st.tabs(["🌍 Globe View", "📐 3D Arc View", "🗺️ Multi-Launch"])
    with tabs[0]: _globe_view()
    with tabs[1]: _arc_view()
    with tabs[2]: _multi_launch()


def _compute_arc(lat0, lon0, bearing_deg, v0, angle_deg, h0_km=80, dt=5.0):
    """
    Compute a ground-track and altitude profile for a trajectory.
    Returns list of (lat, lon, alt_km) tuples along the arc.
    """
    sim = BallisticTrajectory(
        launch_angle_deg=angle_deg,
        burnout_velocity_ms=v0,
        burnout_altitude_m=h0_km * 1000,
        cd_model="cone",
        dt=dt,
    )
    pts = sim.simulate(max_time=5000)
    total_range_km = pts[-1].range_km if pts else 1

    results = []
    bearing_rad = math.radians(bearing_deg)
    lat0_r = math.radians(lat0)
    lon0_r = math.radians(lon0)
    R = 6371.0  # km

    for p in pts:
        d = p.range_km / R  # angular distance in radians
        lat_r = math.asin(
            math.sin(lat0_r) * math.cos(d) +
            math.cos(lat0_r) * math.sin(d) * math.cos(bearing_rad)
        )
        lon_r = lon0_r + math.atan2(
            math.sin(bearing_rad) * math.sin(d) * math.cos(lat0_r),
            math.cos(d) - math.sin(lat0_r) * math.sin(lat_r)
        )
        results.append((math.degrees(lat_r), math.degrees(lon_r), p.altitude_km))

    return results, pts


def _latlon_to_xyz(lat_deg, lon_deg, alt_km=0, R=6371, alt_scale=1.0):
    """Convert lat/lon/alt to Cartesian for 3D sphere."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    r   = R + alt_km * alt_scale
    x   = r * math.cos(lat) * math.cos(lon)
    y   = r * math.cos(lat) * math.sin(lon)
    z   = r * math.sin(lat)
    return x, y, z


def _globe_view():
    st.markdown(section_header("🌍 Globe Trajectory"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        lat0    = st.slider("Launch latitude", -80.0, 80.0, 32.0, step=1.0)
        lon0    = st.slider("Launch longitude", -180.0, 180.0, 48.0, step=1.0)
        bearing = st.slider("Bearing (° from North)", 0, 360, 290)
    with col2:
        v0    = st.slider("Burnout velocity (m/s)", 1000, 6000, 3000, step=100)
        angle = st.slider("Launch angle (°)", 15, 75, 45)

    arc, pts = _compute_arc(lat0, lon0, bearing, v0, angle, dt=10.0)

    # Mapbox globe view
    lats = [a[0] for a in arc]
    lons = [a[1] for a in arc]
    alts = [a[2] for a in arc]
    machs = [p.mach for p in pts[:len(arc)]]

    fig = go.Figure()

    # Ground track
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons,
        mode="lines",
        line=dict(color="#E74C3C", width=2),
        name="Ground track",
        hovertemplate="Lat: %{lat:.2f}°<br>Lon: %{lon:.2f}°<extra>Ground Track</extra>",
    ))

    # Launch / impact markers
    fig.add_trace(go.Scattergeo(
        lat=[lats[0], lats[-1]],
        lon=[lons[0], lons[-1]],
        mode="markers+text",
        marker=dict(size=[14, 12], color=["#27AE60", "#E74C3C"], symbol=["star", "x"]),
        text=["Launch", "Impact"],
        textposition=["top right", "top right"],
        textfont=dict(color="white", size=10),
        name="Events",
        showlegend=False,
    ))

    fig.update_layout(
        geo=dict(
            showland=True, landcolor="#0F1117",
            showocean=True, oceancolor="#080C14",
            showlakes=False,
            showcountries=True, countrycolor="#1E2235",
            showcoastlines=True, coastlinecolor="#1E2235",
            projection_type="orthographic",
            center=dict(lat=float(lat0), lon=float(lon0)),
            bgcolor="#0A0C12",
        ),
        paper_bgcolor="#0A0C12",
        plot_bgcolor="#0A0C12",
        font=dict(color="#B0B8D4"),
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(text="Globe View — Ground Track", font=dict(color="#B0B8D4", size=14)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary
    sum_data = BallisticTrajectory(
        launch_angle_deg=angle, burnout_velocity_ms=v0,
        burnout_altitude_m=80_000, cd_model="cone", dt=10.0,
    ).summary(pts)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Range", f"{sum_data.get('range_km',0):.0f} km")
    col2.metric("Apogee", f"{sum_data.get('apogee_km',0):.0f} km")
    col3.metric("Flight time", f"{sum_data.get('flight_time_s',0)/60:.1f} min")
    col4.metric("Peak Mach", f"Mach {sum_data.get('peak_mach',0):.1f}")


def _arc_view():
    st.markdown(section_header("📐 3D Arc View"), unsafe_allow_html=True)
    st.caption("Altitude exaggerated 20× for visibility on a spherical Earth.")

    col1, col2 = st.columns(2)
    with col1:
        lat0    = st.slider("Launch lat", -80.0, 80.0, 32.0, step=1.0, key="av_lat")
        lon0    = st.slider("Launch lon", -180.0, 180.0, 48.0, step=1.0, key="av_lon")
        bearing = st.slider("Bearing (°)", 0, 360, 290, key="av_brg")
    with col2:
        v0    = st.slider("Burnout v (m/s)", 1000, 6000, 3000, step=100, key="av_v0")
        angle = st.slider("Launch angle (°)", 15, 75, 45, key="av_ang")

    arc, pts = _compute_arc(lat0, lon0, bearing, v0, angle, dt=15.0)
    ALT_SCALE = 20.0
    R = 6371.0

    # Convert arc to XYZ
    xs, ys, zs = [], [], []
    for lat, lon, alt in arc:
        x, y, z = _latlon_to_xyz(lat, lon, alt, R, ALT_SCALE)
        xs.append(x); ys.append(y); zs.append(z)

    # Build Earth sphere surface
    phi   = np.linspace(0, 2*math.pi, 60)
    theta = np.linspace(-math.pi/2, math.pi/2, 30)
    PHI, THETA = np.meshgrid(phi, theta)
    EX = R * np.cos(THETA) * np.cos(PHI)
    EY = R * np.cos(THETA) * np.sin(PHI)
    EZ = R * np.sin(THETA)

    fig = go.Figure()

    # Earth surface
    fig.add_trace(go.Surface(
        x=EX, y=EY, z=EZ,
        colorscale=[[0, "#080C14"], [1, "#0F1117"]],
        showscale=False, opacity=0.85,
        name="Earth",
    ))

    # Trajectory arc
    machs = [p.mach for p in pts[:len(xs)]]
    fig.add_trace(go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode="lines",
        line=dict(
            color=machs,
            colorscale="RdYlGn_r",
            width=5,
            cmin=0, cmax=max(machs) if machs else 10,
            colorbar=dict(title="Mach", x=1.02, thickness=14,
                          tickfont=dict(color="#B0B8D4", size=9)),
        ),
        name="Trajectory",
        hovertemplate="Mach: %{text:.1f}<extra></extra>",
        text=[f"{m:.1f}" for m in machs],
    ))

    # Launch marker
    lx, ly, lz = _latlon_to_xyz(lat0, lon0, 0, R, ALT_SCALE)
    fig.add_trace(go.Scatter3d(
        x=[lx], y=[ly], z=[lz],
        mode="markers",
        marker=dict(size=8, color="#27AE60", symbol="circle"),
        name="Launch",
    ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor="#0A0C12",
        ),
        paper_bgcolor="#0A0C12",
        font=dict(color="#B0B8D4"),
        height=540,
        margin=dict(l=0, r=60, t=30, b=0),
        title=dict(text="3D Arc — Colour = Mach Number (altitude ×20)", font=dict(color="#B0B8D4", size=13)),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _multi_launch():
    st.markdown(section_header("🗺️ Multi-Launch Map"), unsafe_allow_html=True)
    st.markdown("Visualise up to 4 simultaneous trajectories from different launch points.")

    n = st.number_input("Number of launches", 1, 4, 2)

    launches = []
    cols = st.columns(n)
    for i, col in enumerate(cols[:n]):
        with col:
            st.markdown(f"**Launch {i+1}**")
            launches.append({
                "label":   st.text_input("Label", f"L{i+1}", key=f"ml_lbl_{i}"),
                "lat":     st.number_input("Lat", -80.0, 80.0, [32.5, 35.2, 33.0, 30.0][i%4], step=0.5, key=f"ml_lat_{i}"),
                "lon":     st.number_input("Lon", -180.0, 180.0, [48.0, 36.0, 44.0, 51.0][i%4], step=0.5, key=f"ml_lon_{i}"),
                "bearing": st.number_input("Bearing (°)", 0, 360, [295, 285, 300, 270][i%4], key=f"ml_brg_{i}"),
                "v0":      st.number_input("v₀ (m/s)", 1000, 6000, 3000, step=200, key=f"ml_v0_{i}"),
                "angle":   st.number_input("Angle (°)", 15, 75, 45, key=f"ml_ang_{i}"),
            })

    fig = go.Figure()

    for i, launch in enumerate(launches[:n]):
        arc, _ = _compute_arc(
            launch["lat"], launch["lon"],
            launch["bearing"], launch["v0"], launch["angle"], dt=15.0,
        )
        lats = [a[0] for a in arc]
        lons = [a[1] for a in arc]

        fig.add_trace(go.Scattergeo(
            lat=lats, lon=lons,
            mode="lines",
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            name=launch["label"],
        ))
        fig.add_trace(go.Scattergeo(
            lat=[launch["lat"], lats[-1]],
            lon=[launch["lon"], lons[-1]],
            mode="markers",
            marker=dict(size=[12, 10],
                        color=[COLORS[i % len(COLORS)], COLORS[i % len(COLORS)]],
                        symbol=["star", "x"]),
            showlegend=False,
        ))

    fig.update_layout(
        geo=dict(
            showland=True, landcolor="#0F1117",
            showocean=True, oceancolor="#080C14",
            showcountries=True, countrycolor="#1E2235",
            showcoastlines=True, coastlinecolor="#1E2235",
            projection_type="natural earth",
            bgcolor="#0A0C12",
        ),
        paper_bgcolor="#0A0C12",
        font=dict(color="#B0B8D4"),
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=True,
        legend=dict(font=dict(color="#B0B8D4")),
        title=dict(text="Multi-Launch Ground Tracks", font=dict(color="#B0B8D4", size=14)),
    )
    st.plotly_chart(fig, use_container_width=True)

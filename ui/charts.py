"""
ui/charts.py
============
Reusable Plotly chart builders for the Missile Analysis & Research Platform.

All chart functions take plain Python data and return Plotly figure objects.
Pages call st.plotly_chart(fig, use_container_width=True).

Charts in this module are intentionally for educational and analytical
reference purposes — range comparisons, historical timelines, propulsion
parameter curves, etc.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Optional

# ── Brand colors ──────────────────────────────────────────────────────────────
COLORS = [
    "#E74C3C",  # 0  red (primary)
    "#E67E22",  # 1  orange
    "#F1C40F",  # 2  amber
    "#27AE60",  # 3  green
    "#2980B9",  # 4  blue
    "#8E44AD",  # 5  purple
    "#1ABC9C",  # 6  teal
    "#95A5A6",  # 7  grey
]

CHART_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#141824",
    font=dict(color="#6B6F84", family="Inter, sans-serif", size=12),
    xaxis=dict(gridcolor="#1E2235", linecolor="#1E2235", zeroline=False),
    yaxis=dict(gridcolor="#1E2235", linecolor="#1E2235", zeroline=False),
    margin=dict(l=55, r=20, t=50, b=50),
)


def apply_theme(fig: Optional[go.Figure] = None, title: str = "") -> dict:
    """Return a layout dict applying the platform dark theme."""
    layout = {**CHART_THEME}
    if title:
        layout["title"] = dict(text=title, font=dict(color="#E8E8F0", size=14))
    if fig is None:
        return layout
    fig.update_layout(**layout)
    return fig


# ── Category color map ────────────────────────────────────────────────────────
CATEGORY_COLORS = {
    "SRBM":    "#E74C3C",
    "MRBM":    "#E67E22",
    "IRBM":    "#F39C12",
    "ICBM":    "#8E44AD",
    "ADV-BM":  "#9B59B6",
    "Hypers":  "#2980B9",
    "Cruise":  "#27AE60",
    "Anti-Ship": "#1ABC9C",
    "Loitering": "#95A5A6",
}

COUNTRY_COLORS = {
    "Iran":         "#E74C3C",
    "United States": "#2980B9",
    "Russia":        "#E67E22",
    "China":         "#F1C40F",
    "Israel":        "#27AE60",
    "North Korea":   "#8E44AD",
    "Other":         "#95A5A6",
}


# ── Database charts ────────────────────────────────────────────────────────────

def range_comparison_chart(missiles: List[Dict], selected_cats: List[str]) -> go.Figure:
    """
    Horizontal bar chart comparing missile ranges by category.
    missiles: list of dicts with keys: name, range_km, category, country
    """
    filtered = [m for m in missiles if m.get("category") in selected_cats]
    filtered.sort(key=lambda x: x.get("range_km", 0))

    names      = [m["name"] for m in filtered]
    ranges     = [m.get("range_km", 0) for m in filtered]
    categories = [m.get("category", "Other") for m in filtered]
    bar_colors = [CATEGORY_COLORS.get(c, "#95A5A6") for c in categories]

    fig = go.Figure(go.Bar(
        x=ranges, y=names,
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Range: %{x:,} km<extra></extra>",
    ))
    fig.update_layout(
        **apply_theme(title="Missile Range Comparison (km)"),
        height=max(300, len(filtered) * 28 + 80),
        showlegend=False,
    )
    fig.update_xaxes(title_text="Range (km)")
    return fig


def payload_vs_range_scatter(missiles: List[Dict]) -> go.Figure:
    """
    Scatter plot: payload (kg) vs range (km), colored by category.
    """
    fig = go.Figure()
    categories = list(set(m.get("category", "Other") for m in missiles))

    for cat in categories:
        ms = [m for m in missiles if m.get("category") == cat]
        fig.add_trace(go.Scatter(
            x=[m.get("range_km", 0) for m in ms],
            y=[m.get("payload_kg", 0) for m in ms],
            mode="markers+text",
            name=cat,
            text=[m["name"] for m in ms],
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(
                size=10,
                color=CATEGORY_COLORS.get(cat, "#95A5A6"),
                line=dict(width=1, color="rgba(255,255,255,0.2)"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Range: %{x:,} km<br>"
                "Payload: %{y:,} kg<extra></extra>"
            ),
        ))

    fig.update_layout(
        **apply_theme(title="Payload vs Range"),
        height=420,
        showlegend=True,
    )
    fig.update_xaxes(**{"title": {"text": "Range (km)", "font": {"size": 11}},
                        "gridcolor": "#1E2235", "zeroline": False, "linecolor": "#1E2235",
                        "tickfont": {"size": 10}})
    fig.update_yaxes(**{"title": {"text": "Payload (kg)", "font": {"size": 11}},
                        "gridcolor": "#1E2235", "zeroline": False, "linecolor": "#1E2235",
                        "tickfont": {"size": 10}})
    return fig


def mach_comparison_chart(missiles: List[Dict]) -> go.Figure:
    """Bar chart: peak Mach number per missile."""
    missiles_sorted = sorted(missiles, key=lambda m: m.get("peak_mach", 0), reverse=True)
    names  = [m["name"] for m in missiles_sorted]
    machs  = [m.get("peak_mach", 0) for m in missiles_sorted]
    colors = [
        COLORS[0] if v >= 5 else  # hypersonic
        COLORS[1] if v >= 2 else  # supersonic
        COLORS[3]                  # subsonic
        for v in machs
    ]

    fig = go.Figure(go.Bar(
        x=names, y=machs,
        marker=dict(color=colors),
        hovertemplate="<b>%{x}</b><br>Peak Mach: %{y}<extra></extra>",
    ))
    fig.add_hline(y=5, line_dash="dash", line_color="#2980B9",
                  annotation_text="Hypersonic threshold (Mach 5)")
    fig.update_layout(
        **apply_theme(title="Peak Mach Number by Missile"),
        height=350,
        showlegend=False,
    )
    fig.update_yaxes(title_text="Peak Mach Number")
    return fig


def country_distribution_pie(missiles: List[Dict]) -> go.Figure:
    """Pie chart of missiles by country."""
    from collections import Counter
    counts = Counter(m.get("country", "Other") for m in missiles)
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [COUNTRY_COLORS.get(l, "#95A5A6") for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors, line=dict(color="#0A0C12", width=2)),
        hovertemplate="<b>%{label}</b>: %{value} systems<extra></extra>",
        textfont=dict(size=11),
    ))
    fig.update_layout(**apply_theme(title="Systems by Country"), height=320)
    return fig


# ── Historical timeline charts ────────────────────────────────────────────────

def escalation_timeline_chart(events: List[Dict]) -> go.Figure:
    """
    Bar chart showing projectiles fired per historical event.
    events: list of dicts with keys: label, missiles_fired, intercepted, year
    """
    labels    = [e["label"] for e in events]
    fired     = [e.get("missiles_fired", 0) for e in events]
    intercept = [e.get("intercepted", 0) for e in events]
    penetrated = [max(0, f - i) for f, i in zip(fired, intercept)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Intercepted", x=labels, y=intercept,
        marker_color=COLORS[3],
        hovertemplate="%{x}<br>Intercepted: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Penetrated", x=labels, y=penetrated,
        marker_color=COLORS[0],
        hovertemplate="%{x}<br>Penetrated: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **apply_theme(title="Historical Strike Events — Intercept Outcomes"),
        barmode="stack",
        height=380,
        showlegend=True,
    )
    fig.update_yaxes(title_text="Projectiles")
    return fig


# ── Education / physics charts ────────────────────────────────────────────────

def isp_comparison_chart() -> go.Figure:
    """
    Educational chart: Specific impulse (Isp) by propellant type.
    Values from standard aerospace references (Sutton & Biblarz, 9th ed).
    """
    propellants = [
        "Cold Gas (N₂)",
        "Monopropellant (N₂H₄)",
        "Solid (AP/HTPB)",
        "Liquid (UDMH/N₂O₄)",
        "Liquid (LOX/RP-1)",
        "Liquid (LOX/LH₂)",
        "Nuclear Thermal (H₂)",
    ]
    isp_vac = [65, 220, 280, 315, 340, 450, 900]
    colors  = [COLORS[7], COLORS[6], COLORS[1], COLORS[0], COLORS[4], COLORS[2], COLORS[5]]

    fig = go.Figure(go.Bar(
        x=isp_vac, y=propellants,
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="<b>%{y}</b><br>Isp (vac): ~%{x} s<extra></extra>",
    ))
    fig.update_layout(
        **apply_theme(title="Specific Impulse (Isp) by Propellant Type — Vacuum"),
        height=380, showlegend=False,
    )
    fig.update_xaxes(title_text="Specific Impulse, Isp (seconds)")
    return fig


def atmospheric_density_profile() -> go.Figure:
    """
    Educational chart: ISA atmospheric density vs altitude.
    Uses the International Standard Atmosphere model.
    """
    import math
    altitudes = list(range(0, 90001, 1000))  # 0–90 km

    def isa_density(h_m: float) -> float:
        RHO0, H_SCALE = 1.225, 8500.0
        if h_m <= 11000:
            T = 288.15 - 0.0065 * h_m
            return RHO0 * (T / 288.15) ** 4.256
        elif h_m <= 20000:
            return 0.3639 * math.exp(-0.0001577 * (h_m - 11000))
        else:
            return RHO0 * math.exp(-h_m / H_SCALE) * 0.05

    densities = [isa_density(h) for h in altitudes]
    alt_km    = [h / 1000 for h in altitudes]

    fig = go.Figure(go.Scatter(
        x=densities, y=alt_km,
        mode="lines",
        line=dict(color=COLORS[4], width=2),
        fill="tozerox",
        fillcolor="rgba(41,128,185,0.10)",
        hovertemplate="Alt: %{y} km<br>ρ: %{x:.4f} kg/m³<extra></extra>",
    ))

    # Regime annotations
    for alt, label, color in [
        (11, "Tropopause (11 km)", COLORS[1]),
        (20, "Stratopause (20 km)", COLORS[2]),
        (50, "Mesopause (~50 km)", COLORS[3]),
        (80, "Kármán line (~80 km)", COLORS[5]),
    ]:
        fig.add_hline(y=alt, line_dash="dot", line_color=color,
                      annotation_text=label, annotation_font_size=9)

    fig.update_layout(
        **apply_theme(title="ISA Atmospheric Density Profile"),
        height=420, showlegend=False,
    )
    fig.update_xaxes(title_text="Air Density (kg/m³)", type="log")
    fig.update_yaxes(title_text="Altitude (km)")
    return fig


def rocket_equation_chart() -> go.Figure:
    """
    Educational chart: delta-V vs mass ratio for several Isp values.
    Tsiolkovsky rocket equation: Δv = Isp × g₀ × ln(m₀/mf)
    """
    import math
    G0 = 9.80665
    mass_ratios = [x / 10 for x in range(10, 101)]  # 1.0 – 10.0

    isp_values = {
        "Solid (Isp=280s)":        (280, COLORS[1]),
        "Liquid UDMH (Isp=315s)":  (315, COLORS[0]),
        "LOX/RP-1 (Isp=340s)":     (340, COLORS[4]),
        "LOX/LH₂ (Isp=450s)":      (450, COLORS[2]),
    }

    fig = go.Figure()
    for label, (isp, color) in isp_values.items():
        dvs = [isp * G0 * math.log(mr) / 1000 for mr in mass_ratios]  # km/s
        fig.add_trace(go.Scatter(
            x=mass_ratios, y=dvs,
            name=label, mode="lines",
            line=dict(color=color, width=2),
            hovertemplate=f"{label}<br>Mass ratio: %{{x:.1f}}<br>Δv: %{{y:.2f}} km/s<extra></extra>",
        ))

    fig.update_layout(
        **apply_theme(title="Tsiolkovsky Rocket Equation — Δv vs Mass Ratio"),
        height=380, showlegend=True,
    )
    fig.update_xaxes(title_text="Mass Ratio (m₀/mf)")
    fig.update_yaxes(title_text="Delta-V (km/s)")
    return fig


def treaty_timeline_chart() -> go.Figure:
    """Timeline of major arms control treaties."""
    treaties = [
        {"name": "Nuclear Non-Proliferation Treaty (NPT)", "start": 1968, "end": 2099, "color": COLORS[3]},
        {"name": "SALT I", "start": 1972, "end": 1979, "color": COLORS[4]},
        {"name": "SALT II", "start": 1979, "end": 1986, "color": COLORS[4]},
        {"name": "INF Treaty", "start": 1987, "end": 2019, "color": COLORS[1]},
        {"name": "START I", "start": 1991, "end": 2009, "color": COLORS[2]},
        {"name": "Moscow Treaty (SORT)", "start": 2002, "end": 2011, "color": COLORS[5]},
        {"name": "New START", "start": 2011, "end": 2026, "color": COLORS[2]},
        {"name": "MTCR (Regime, not treaty)", "start": 1987, "end": 2099, "color": COLORS[7]},
    ]

    fig = go.Figure()
    for i, t in enumerate(treaties):
        fig.add_trace(go.Bar(
            x=[min(t["end"], 2026) - t["start"]],
            y=[t["name"]],
            base=[t["start"]],
            orientation="h",
            marker_color=t["color"],
            marker_line_width=0,
            name=t["name"],
            showlegend=False,
            hovertemplate=f"<b>{t['name']}</b><br>{t['start']}–{min(t['end'],2026)}<extra></extra>",
        ))

    fig.add_vline(x=2026, line_dash="dash", line_color=COLORS[0],
                  annotation_text="2026", annotation_font_color=COLORS[0])
    fig.add_vline(x=2019, line_dash="dot", line_color=COLORS[1],
                  annotation_text="INF collapse", annotation_font_size=9)

    fig.update_layout(
        **apply_theme(title="Major Arms Control Treaties — Timeline"),
        height=380, showlegend=False,
        xaxis=dict(range=[1965, 2030], gridcolor="#1E2235", linecolor="#1E2235",
                   tickfont={"size": 10}, zeroline=False),
    )
    return fig

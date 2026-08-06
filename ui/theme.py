"""
ui/theme.py
============
Global design system for the Missile Analysis & Research Platform.

One authoritative source of truth for all CSS, colour tokens, Plotly styling,
and HTML component builders used across all pages of the platform.

USAGE
-----
  # app.py — inject once before routing:
  from ui.theme import inject_global_css
  inject_global_css()

  # Any module — HTML components:
  from ui.theme import card, badge, metric_box, section_header
  st.markdown(section_header("📡 Analysis"), unsafe_allow_html=True)
  st.markdown(card("Body text", variant="info"), unsafe_allow_html=True)

  # Any module — Plotly charts:
  from ui.theme import plotly_layout, plotly_axis
  fig.update_layout(**plotly_layout(height=360))
  fig.update_xaxes(**plotly_axis("Range (km)"))
"""

from __future__ import annotations
from typing import Optional
import streamlit as st


# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS  — the single source of truth
# ═══════════════════════════════════════════════════════════════════════════════

# ── Background palette ────────────────────────────────────────────────────────
BG_APP        = "#0A0C12"
BG_SIDEBAR    = "#0D101A"
BG_CARD       = "#141824"
BG_CARD_DEEP  = "#0F1219"
BG_PLOT       = "rgba(10,12,18,0.97)"

# ── Accent — military red ─────────────────────────────────────────────────────
ACCENT        = "#C0392B"
ACCENT_DIM    = "#96281B"
ACCENT_BRIGHT = "#E74C3C"

# ── Text ─────────────────────────────────────────────────────────────────────
TEXT_PRIMARY  = "#E8E8F0"
TEXT_BODY     = "#B8BCC8"
TEXT_MUTED    = "#6B6F84"

# ── Borders ──────────────────────────────────────────────────────────────────
BORDER        = "#1E2235"
BORDER_ACCENT = "#4A1C1C"

# ── Semantic colours ─────────────────────────────────────────────────────────
COLOR_SUCCESS = "#27AE60"
COLOR_WARNING = "#E67E22"
COLOR_DANGER  = "#C0392B"
COLOR_BLUE    = "#2980B9"
COLOR_PURPLE  = "#8E44AD"

# ── Semantic tints ────────────────────────────────────────────────────────────
BG_SUCCESS = "#071510";  BORDER_SUCCESS = "#145A32"
BG_WARNING = "#150E05";  BORDER_WARNING = "#784212"
BG_DANGER  = "#160506";  BORDER_DANGER  = "#7B241C"
BG_INFO    = "#071524";  BORDER_INFO    = "#1A5276"
BG_PURPLE  = "#0E0715";  BORDER_PURPLE  = "#6C3483"

# ── Plotly ────────────────────────────────────────────────────────────────────
PLOT_GRID  = "#1E2A3A"
PLOT_TEXT  = "#6B6F84"

# ── Radii ─────────────────────────────────────────────────────────────────────
R_SM = "6px"; R_MD = "10px"; R_LG = "16px"

# ── Font sizes ────────────────────────────────────────────────────────────────
FS_XS = "0.65rem"; FS_SM = "0.78rem"; FS_BODY = "0.88rem"
FS_MD = "1.0rem";  FS_LG = "1.2rem";  FS_XL   = "1.5rem"


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS STRING
# ═══════════════════════════════════════════════════════════════════════════════

_CSS = f"""
<style>
/* ═══ MISSILE ANALYSIS PLATFORM · GLOBAL STYLES ══════════════════════════════
   Injected once from app.py via inject_global_css().
   ══════════════════════════════════════════════════════════════════════════ */

/* ── App base ──────────────────────────────────────────────────────────── */
.stApp {{ background-color: {BG_APP}; }}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {BG_SIDEBAR} 0%, {BG_APP} 100%);
    border-right: 1px solid {BORDER};
}}

/* ── Metric cards ──────────────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {R_LG};
    padding: 16px;
    transition: border-color 0.2s ease;
}}
[data-testid="metric-container"]:hover {{ border-color: {ACCENT_DIM}; }}

/* ── Buttons ────────────────────────────────────────────────────────────── */
.stButton > button {{
    border-radius: {R_MD};
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    font-weight: 500;
}}
.stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(192,57,43,0.20);
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {ACCENT} 0%, {ACCENT_DIM} 100%);
    border: none;
    color: #FAFAFA;
    font-weight: 600;
}}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: {BG_CARD_DEEP};
    border-radius: {R_MD} {R_MD} 0 0;
    border-bottom: 2px solid {BORDER};
    gap: 2px;
    padding: 4px 4px 0;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: {R_SM} {R_SM} 0 0;
    color: {TEXT_MUTED};
    font-weight: 500;
    font-size: {FS_BODY};
    padding: 8px 18px;
    transition: color 0.2s, background 0.2s;
}}
.stTabs [aria-selected="true"] {{
    background: {BG_CARD} !important;
    color: {ACCENT_BRIGHT} !important;
    font-weight: 600;
    border-bottom: 2px solid {ACCENT};
}}
.stTabs [data-baseweb="tab-panel"] {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-top: none;
    border-radius: 0 0 {R_MD} {R_MD};
    padding: 20px;
}}

/* ── Expanders ──────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: {R_MD} !important;
    font-weight: 600;
    color: {TEXT_PRIMARY} !important;
}}
.streamlit-expanderHeader:hover {{
    background: {BG_CARD_DEEP} !important;
    border-color: {ACCENT_DIM} !important;
}}

/* ── Inputs ─────────────────────────────────────────────────────────────── */
[data-baseweb="select"] > div {{
    background: {BG_CARD_DEEP} !important;
    border: 1px solid {BORDER} !important;
    border-radius: {R_MD} !important;
}}
[data-baseweb="input"] input {{
    background: {BG_CARD_DEEP} !important;
    border-color: {BORDER} !important;
    color: {TEXT_PRIMARY} !important;
    border-radius: {R_MD} !important;
}}

/* ── Headings ────────────────────────────────────────────────────────────── */
h1 {{ color: {ACCENT_BRIGHT};  font-weight: 700; letter-spacing: -0.02em; }}
h2 {{ color: {TEXT_PRIMARY};   font-weight: 600; }}
h3 {{ color: {TEXT_PRIMARY};   font-weight: 600; }}

/* ── Sidebar divider ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] hr {{ border-color: {BORDER}; margin: 6px 0; }}

/* ══ PLATFORM CARD SYSTEM ════════════════════════════════════════════════════ */
.mp-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER_ACCENT};
    border-radius: {R_MD};
    padding: 16px 20px;
    margin: 8px 0;
    color: {TEXT_BODY};
    font-size: {FS_BODY};
    line-height: 1.7;
}}
.mp-card-success {{ background:{BG_SUCCESS}; border-color:{BORDER_SUCCESS}; }}
.mp-card-warning {{ background:{BG_WARNING}; border-color:{BORDER_WARNING}; }}
.mp-card-danger  {{ background:{BG_DANGER};  border-color:{BORDER_DANGER};  }}
.mp-card-info    {{ background:{BG_INFO};    border-color:{BORDER_INFO};    }}
.mp-card-purple  {{ background:{BG_PURPLE};  border-color:{BORDER_PURPLE};  }}
.mp-card-plain   {{ background:{BG_CARD_DEEP}; border-color:{BORDER};       }}
.mp-card-accent  {{
    border-left: 4px solid {ACCENT};
    border-top: 1px solid {BORDER};
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    background: {BG_CARD};
    border-radius: 0 {R_MD} {R_MD} 0;
    padding: 10px 16px;
    margin: 4px 0;
}}

/* ══ HEADERS ════════════════════════════════════════════════════════════════ */
.mp-section-header {{
    font-size: {FS_LG};
    font-weight: 700;
    color: {ACCENT_BRIGHT};
    border-bottom: 2px solid {BORDER};
    padding-bottom: 7px;
    margin-top: 20px;
    margin-bottom: 6px;
    letter-spacing: -0.01em;
}}
.mp-sub-header {{
    font-size: {FS_MD};
    font-weight: 600;
    color: {TEXT_PRIMARY};
    margin-top: 14px;
    margin-bottom: 4px;
}}
.mp-label {{
    font-size: {FS_SM};
    font-weight: 600;
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}}

/* ══ BADGE SYSTEM ══════════════════════════════════════════════════════════ */
.mp-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: {FS_XS};
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    vertical-align: middle;
    line-height: 1.6;
}}
.mp-badge-info    {{ background:{BG_INFO};    color:#5DADE2;          border:1px solid {BORDER_INFO};    }}
.mp-badge-success {{ background:{BG_SUCCESS}; color:{COLOR_SUCCESS};  border:1px solid {BORDER_SUCCESS}; }}
.mp-badge-warning {{ background:{BG_WARNING}; color:{COLOR_WARNING};  border:1px solid {BORDER_WARNING}; }}
.mp-badge-danger  {{ background:{BG_DANGER};  color:{COLOR_DANGER};   border:1px solid {BORDER_DANGER};  }}
.mp-badge-purple  {{ background:{BG_PURPLE};  color:{COLOR_PURPLE};   border:1px solid {BORDER_PURPLE};  }}
.mp-badge-muted   {{ background:{BG_CARD_DEEP}; color:{TEXT_MUTED};   border:1px solid {BORDER};         }}
.mp-badge-pro     {{ background:rgba(192,57,43,0.15); color:{ACCENT_BRIGHT}; border:1px solid {ACCENT};  }}

/* ══ METRIC BOX ════════════════════════════════════════════════════════════ */
.mp-metric-box {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {R_MD};
    padding: 16px 12px;
    text-align: center;
    transition: border-color 0.2s ease;
}}
.mp-metric-box:hover {{ border-color: {ACCENT_DIM}; }}
.mp-metric-value {{
    font-size: 1.9rem;
    font-weight: 700;
    color: {ACCENT_BRIGHT};
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}}
.mp-metric-label {{
    font-size: {FS_XS};
    color: {TEXT_MUTED};
    margin-top: 3px;
    line-height: 1.35;
    font-weight: 500;
}}

/* ══ MISSILE CARD ══════════════════════════════════════════════════════════ */
.missile-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-left: 3px solid {ACCENT};
    border-radius: {R_MD};
    padding: 14px 18px;
    margin: 6px 0;
    transition: border-color 0.2s ease;
}}
.missile-card:hover {{ border-color: {ACCENT}; }}
.missile-card-name {{
    font-size: {FS_MD};
    font-weight: 700;
    color: {TEXT_PRIMARY};
    margin-bottom: 4px;
}}
.missile-card-meta {{
    font-size: {FS_SM};
    color: {TEXT_MUTED};
}}

/* ══ TREATY CARD ══════════════════════════════════════════════════════════ */
.treaty-card {{
    background: {BG_INFO};
    border: 1px solid {BORDER_INFO};
    border-radius: {R_MD};
    padding: 16px 20px;
    margin: 8px 0;
}}

/* ══ TIMELINE ═════════════════════════════════════════════════════════════ */
.timeline-event {{
    border-left: 3px solid {ACCENT};
    padding-left: 16px;
    margin: 12px 0 12px 8px;
    position: relative;
}}
.timeline-event::before {{
    content: '';
    width: 10px;
    height: 10px;
    background: {ACCENT};
    border-radius: 50%;
    position: absolute;
    left: -7px;
    top: 4px;
}}
.timeline-date {{
    font-size: {FS_SM};
    color: {ACCENT_BRIGHT};
    font-weight: 700;
    margin-bottom: 2px;
}}
.timeline-title {{
    font-size: {FS_MD};
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}
.timeline-body {{
    font-size: {FS_SM};
    color: {TEXT_BODY};
    margin-top: 3px;
    line-height: 1.6;
}}

/* ══ UPGRADE GATE ══════════════════════════════════════════════════════════ */
.mp-gate {{
    background: linear-gradient(135deg, #1A0E0E 0%, {BG_CARD_DEEP} 100%);
    border: 1.5px solid {ACCENT};
    border-radius: {R_LG};
    padding: 40px 32px;
    text-align: center;
    margin: 40px auto;
    max-width: 600px;
}}
.mp-gate-icon  {{ font-size:3rem; margin-bottom:12px; }}
.mp-gate-title {{ color:{ACCENT_BRIGHT}; font-size:{FS_XL}; font-weight:700; margin:0 0 10px; }}
.mp-gate-body  {{ color:#CCCCCC; font-size:0.93rem; margin:0; }}

/* ══ FEATURE ROW ══════════════════════════════════════════════════════════ */
.mp-feature-row {{
    display:flex; align-items:flex-start; gap:12px;
    padding:8px 12px; margin:4px 0;
    background:{BG_CARD}; border-radius:{R_MD};
    border-left:3px solid rgba(192,57,43,0.3);
}}
.mp-feature-check {{ color:{ACCENT_BRIGHT}; font-size:{FS_BODY}; padding-top:2px; }}
.mp-feature-text  {{ font-size:0.9rem; color:#CCCCCC; }}

/* ══ DATA TABLE ════════════════════════════════════════════════════════════ */
.mp-table {{ width:100%; border-collapse:collapse; font-size:{FS_BODY}; color:{TEXT_BODY}; border:1px solid {BORDER}; border-radius:{R_MD}; overflow:hidden; }}
.mp-table th {{ background:{BG_CARD_DEEP}; color:{TEXT_MUTED}; font-weight:600; font-size:{FS_XS}; text-transform:uppercase; letter-spacing:0.07em; padding:10px 14px; border-bottom:1px solid {BORDER}; text-align:left; }}
.mp-table td {{ padding:9px 14px; border-bottom:1px solid {BORDER}; }}
.mp-table tr:last-child td {{ border-bottom:none; }}
.mp-table tr:hover td {{ background:{BG_CARD_DEEP}; }}

</style>
"""


# ═══════════════════════════════════════════════════════════════════════════════
# INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

def inject_global_css() -> None:
    """
    Inject the global CSS into the Streamlit app.
    Call exactly ONCE from app.py main(), before the router.
    """
    st.markdown(_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HTML COMPONENT BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def section_header(text: str) -> str:
    return f"<div class='mp-section-header'>{text}</div>"


def sub_header(text: str) -> str:
    return f"<div class='mp-sub-header'>{text}</div>"


def label(text: str) -> str:
    return f"<div class='mp-label'>{text}</div>"


def card(content: str, variant: str = "default") -> str:
    """
    Styled card container.
    variant: "default" | "success" | "warning" | "danger" | "info" | "purple" | "plain" | "accent"
    """
    cls_map = {
        "default": "mp-card",
        "success": "mp-card mp-card-success",
        "warning": "mp-card mp-card-warning",
        "danger":  "mp-card mp-card-danger",
        "info":    "mp-card mp-card-info",
        "purple":  "mp-card mp-card-purple",
        "plain":   "mp-card mp-card-plain",
        "accent":  "mp-card mp-card-accent",
    }
    return f"<div class='{cls_map.get(variant, 'mp-card')}'>{content}</div>"


def badge(text: str, variant: str = "info") -> str:
    cls_map = {
        "info": "mp-badge-info", "success": "mp-badge-success",
        "warning": "mp-badge-warning", "danger": "mp-badge-danger",
        "purple": "mp-badge-purple", "muted": "mp-badge-muted", "pro": "mp-badge-pro",
    }
    cls = cls_map.get(variant, "mp-badge-info")
    return f"<span class='mp-badge {cls}'>{text}</span>"


def metric_box(icon: str, value: str, label_text: str) -> str:
    lbl = label_text.replace("\n", "<br>")
    return (
        f"<div class='mp-metric-box'>"
        f"<div style='font-size:1.5rem;margin-bottom:4px'>{icon}</div>"
        f"<div class='mp-metric-value'>{value}</div>"
        f"<div class='mp-metric-label'>{lbl}</div>"
        f"</div>"
    )


def missile_card(name: str, category: str, country: str, range_km: int,
                 mach: float, prop: str) -> str:
    return (
        f"<div class='missile-card'>"
        f"<div class='missile-card-name'>🚀 {name}</div>"
        f"<div class='missile-card-meta'>"
        f"{badge(category, 'danger')} &nbsp;"
        f"{badge(country, 'info')} &nbsp;"
        f"{badge(prop, 'muted')}"
        f"</div>"
        f"<div style='margin-top:8px; display:flex; gap:24px; font-size:0.82rem; color:#B8BCC8;'>"
        f"<span><strong>Range:</strong> {range_km:,} km</span>"
        f"<span><strong>Mach:</strong> {mach}</span>"
        f"</div>"
        f"</div>"
    )


def timeline_event(date: str, title: str, body: str) -> str:
    return (
        f"<div class='timeline-event'>"
        f"<div class='timeline-date'>{date}</div>"
        f"<div class='timeline-title'>{title}</div>"
        f"<div class='timeline-body'>{body}</div>"
        f"</div>"
    )


def feature_row(title: str, description: str) -> str:
    return (
        f"<div class='mp-feature-row'>"
        f"<span class='mp-feature-check'>✓</span>"
        f"<span class='mp-feature-text'>"
        f"<strong style='color:{TEXT_PRIMARY}'>{title}</strong> — {description}"
        f"</span></div>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PLOTLY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def plotly_layout(
    height: int = 360,
    showlegend: Optional[bool] = None,
    barmode: Optional[str] = None,
    title: Optional[str] = None,
    margin: Optional[dict] = None,
    **kwargs,
) -> dict:
    base = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor":  BG_PLOT,
        "font":          {"color": PLOT_TEXT, "size": 11},
        "height":        height,
        "margin":        margin or {"t": 50 if title else 30, "b": 45, "l": 55, "r": 20},
        "legend": {
            "bgcolor":     "rgba(10,12,18,0.9)",
            "bordercolor": PLOT_GRID,
            "borderwidth": 1,
            "font":        {"size": 10, "color": PLOT_TEXT},
        },
    }
    if showlegend is not None: base["showlegend"] = showlegend
    if barmode    is not None: base["barmode"]    = barmode
    if title:
        base["title"] = {"text": title, "font": {"size": 13, "color": TEXT_PRIMARY}, "x": 0.01, "xanchor": "left"}
    base.update(kwargs)
    return base


def plotly_axis(
    title: str = "",
    axis_range: Optional[list] = None,
    axis_type: Optional[str] = None,
    **kwargs,
) -> dict:
    base = {
        "title":      {"text": title, "font": {"size": 11, "color": PLOT_TEXT}},
        "gridcolor":  PLOT_GRID,
        "tickfont":   {"color": PLOT_TEXT, "size": 10},
        "zeroline":   False,
        "linecolor":  PLOT_GRID,
    }
    if axis_range is not None: base["range"] = axis_range
    if axis_type  is not None: base["type"]  = axis_type
    base.update(kwargs)
    return base


# Token aliases
_ACCENT   = ACCENT; _TEXT = TEXT_PRIMARY; _MUTED = TEXT_MUTED
_BG_CARD  = BG_CARD; _BG_PLOT = BG_PLOT; _GRID = PLOT_GRID
_BORDER   = BORDER_ACCENT
_GREEN    = COLOR_SUCCESS; _ORANGE = COLOR_WARNING
_RED      = COLOR_DANGER;  _PURPLE = COLOR_PURPLE

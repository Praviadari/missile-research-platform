"""auth/auth_guard.py — Feature-gate decorator and inline guard."""
import functools, streamlit as st
from auth.auth import can_access, is_authenticated, current_tier

TIER_FEATURES = {
    "pro": [
        ("📈 Trajectory Simulator",   "Physics-based 2D trajectory with atmosphere and drag"),
        ("🔥 Propulsion Analysis",    "Isp curves, staging optimisation, mass fraction explorer"),
        ("⚡ Hypersonic Lab",          "HGV, scramjet, thermal management deep-dive"),
        ("🛡️ Defense Systems Lab",    "Layered defense engagement envelope reference"),
        ("💥 Saturation Modeler",     "Monte Carlo saturation analysis with historical scenarios"),
        ("🛠️ Design Lab",            "7-step guided missile design research workflow"),
        ("🌐 3D Visualizer",          "Three-dimensional trajectory and engagement visualizer"),
    ],
}

def gate_page(required_tier: str, page_name: str) -> bool:
    if can_access(page_name.lower().replace(" ","_")):
        return True
    tier = current_tier()
    tier_order = {"anon":0,"free":1,"pro":2,"enterprise":3}
    req_order  = {"free":1,"pro":2,"enterprise":3}
    if tier_order.get(tier,0) >= req_order.get(required_tier,2):
        return True

    st.markdown(
        f"""<div class='mp-gate'>
        <div class='mp-gate-icon'>🔒</div>
        <div class='mp-gate-title'>{page_name}</div>
        <div class='mp-gate-body'>This feature requires a <strong>Pro</strong> subscription.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    features = TIER_FEATURES.get(required_tier, [])
    if features:
        from ui.theme import feature_row
        st.markdown("**Pro includes:**")
        for title, desc in features:
            st.markdown(feature_row(title, desc), unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("⚡ Upgrade to Pro", type="primary", use_container_width=True):
            st.session_state["auth.show_auth_modal"] = True
            st.session_state["auth.auth_mode"] = "upgrade"
            st.rerun()
    return False

def require_tier(tier: str):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not gate_page(tier, fn.__name__):
                return
            return fn(*args, **kwargs)
        return wrapper
    return decorator

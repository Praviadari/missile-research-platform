"""
billing/stripe_billing.py
==========================
Stripe subscription management for the Missile Research Platform.

Handles:
  - Creating Stripe customer for new users
  - Checking active subscription status
  - Rendering upgrade UI with payment link
  - Webhook handling for subscription lifecycle events

Requires: STRIPE_SECRET_KEY, STRIPE_PRO_PRICE_ID, STRIPE_WEBHOOK_SECRET

USAGE
-----
    from billing.stripe_billing import get_tier_from_stripe, render_upgrade_cta

    # Check tier (called during auth setup):
    tier = get_tier_from_stripe(stripe_customer_id)

    # Render upgrade button on any page:
    render_upgrade_cta()
"""

import os
import logging
import streamlit as st

logger = logging.getLogger(__name__)

STRIPE_SECRET_KEY       = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRO_PRICE_ID     = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_WEBHOOK_SECRET   = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PAYMENT_LINK     = os.getenv("STRIPE_PAYMENT_LINK", "#")
ENTERPRISE_CALENDLY     = os.getenv("ENTERPRISE_CALENDLY", "#")

PRO_MONTHLY_PRICE = "$29"
PRO_ANNUAL_PRICE  = "$249"


def _stripe():
    """Return configured stripe module or None."""
    if not STRIPE_SECRET_KEY:
        return None
    try:
        import stripe as _s
        _s.api_key = STRIPE_SECRET_KEY
        return _s
    except ImportError:
        logger.warning("stripe package not installed")
        return None


def get_tier_from_stripe(customer_id: str | None) -> str:
    """
    Query Stripe for active subscription and return tier string.

    Returns: "pro" | "enterprise" | "free"
    """
    if not customer_id:
        return "free"
    s = _stripe()
    if s is None:
        return "free"
    try:
        subs = s.Subscription.list(customer=customer_id, status="active", limit=5)
        if not subs.data:
            return "free"
        # Check price IDs against known pro/enterprise prices
        enterprise_prices = set(os.getenv("STRIPE_ENTERPRISE_PRICE_IDS", "").split(","))
        for sub in subs.data:
            for item in sub["items"]["data"]:
                if item["price"]["id"] in enterprise_prices:
                    return "enterprise"
        return "pro"
    except Exception as e:
        logger.warning("Stripe tier check failed: %s", e)
        return "free"


def create_customer(email: str, user_id: str) -> str | None:
    """
    Create a Stripe customer record for a new user.
    Returns customer ID string or None on failure.
    """
    s = _stripe()
    if s is None:
        return None
    try:
        customer = s.Customer.create(
            email=email,
            metadata={"supabase_user_id": user_id, "platform": "missile_research_v2"},
        )
        return customer["id"]
    except Exception as e:
        logger.warning("Stripe customer creation failed: %s", e)
        return None


def _tier_from_subscription_obj(obj: dict) -> str:
    """Map a Stripe subscription object to platform tier."""
    if obj.get("status") not in ("active", "trialing"):
        return "free"
    enterprise_prices = {
        x.strip()
        for x in os.getenv("STRIPE_ENTERPRISE_PRICE_IDS", "").split(",")
        if x.strip()
    }
    items = (obj.get("items") or {}).get("data") or []
    for item in items:
        price_id = (item.get("price") or {}).get("id", "")
        if price_id and price_id in enterprise_prices:
            return "enterprise"
    return "pro"


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """
    Handle incoming Stripe webhook event.
    Call from FastAPI POST /stripe/webhook endpoint.

    Persists tier updates to the users table when DATABASE_URL is set.
    """
    s = _stripe()
    if s is None:
        return {"handled": False, "reason": "stripe not configured"}
    try:
        event = s.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise ValueError(f"Webhook verification failed: {e}")

    etype = event["type"]
    obj = event["data"]["object"]
    customer_id = obj.get("customer")
    persisted = False

    if etype in ("customer.subscription.created", "customer.subscription.updated"):
        tier = _tier_from_subscription_obj(obj)
        logger.info("Subscription %s: customer=%s tier=%s", etype, customer_id, tier)
        if customer_id:
            from database.session import update_tier_by_stripe_customer

            persisted = update_tier_by_stripe_customer(customer_id, tier)

    elif etype == "customer.subscription.deleted":
        logger.info("Subscription cancelled: customer=%s", customer_id)
        if customer_id:
            from database.session import update_tier_by_stripe_customer

            persisted = update_tier_by_stripe_customer(customer_id, "free")

    elif etype == "invoice.payment_failed":
        logger.warning("Payment failed: customer=%s", customer_id)

    return {
        "handled": True,
        "event_type": etype,
        "customer_id": customer_id,
        "persisted": persisted,
    }


def render_upgrade_cta(compact: bool = False) -> None:
    """
    Render the Pro upgrade call-to-action in the current Streamlit container.

    compact=True  → single button row
    compact=False → full upgrade wall with feature list
    """
    from ui.theme import card, feature_row

    if not compact:
        st.markdown(
            f"""
            <div class='mp-gate'>
                <div class='mp-gate-icon'>⚡</div>
                <div class='mp-gate-title'>Upgrade to Pro</div>
                <div class='mp-gate-body'>
                    {PRO_MONTHLY_PRICE}/month · {PRO_ANNUAL_PRICE}/year (save 30%)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        features = [
            ("📈 Trajectory Simulator",   "2D physics-based trajectory with ISA atmosphere and drag"),
            ("🔥 Propulsion Analysis",    "Isp curves, multi-stage optimisation, mass fraction explorer"),
            ("⚡ Hypersonic Lab",          "HGV, scramjet, and thermal management reference tools"),
            ("🛡️ Defense Systems Lab",    "Layered defense engagement envelopes, intercept geometry"),
            ("🛠️ Design Lab",            "7-step guided missile design research wizard"),
            ("🌐 3D Visualizer",          "Three-dimensional trajectory and engagement visualizer"),
            ("💾 Saved Searches",         "Persistent workspace — search presets and research notes"),
        ]
        for title, desc in features:
            st.markdown(feature_row(title, desc), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.link_button(
            f"⚡ Upgrade to Pro — {PRO_MONTHLY_PRICE}/mo",
            STRIPE_PAYMENT_LINK,
            use_container_width=True,
            type="primary",
        )
    with col2:
        st.link_button(
            "🏢 Enterprise — Contact Us",
            ENTERPRISE_CALENDLY,
            use_container_width=True,
        )

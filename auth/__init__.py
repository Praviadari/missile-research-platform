"""Authentication package — Supabase Auth + tier gating."""

from auth.auth import can_access, current_tier, is_authenticated, setup, sign_in, sign_out, sign_up

__all__ = [
    "can_access",
    "current_tier",
    "is_authenticated",
    "setup",
    "sign_in",
    "sign_out",
    "sign_up",
]

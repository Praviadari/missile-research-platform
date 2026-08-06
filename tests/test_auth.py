"""
tests/test_auth.py
==================
Unit tests for tier gating (can_access) without Streamlit UI.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Streamlit is imported by auth; provide a minimal session_state stand-in.
import streamlit as st

if not hasattr(st, "session_state") or not isinstance(st.session_state, dict):
    st.session_state = {}  # type: ignore[assignment]

from auth.auth import PRO_PAGES, PUBLIC_PAGES, can_access  # noqa: E402


def _set_tier(tier: str):
    st.session_state["auth.tier"] = tier


class TestCanAccess:
    def test_public_pages_open_to_anon(self):
        _set_tier("anon")
        for key in PUBLIC_PAGES:
            assert can_access(key) is True

    def test_pro_pages_blocked_for_free(self):
        _set_tier("free")
        for key in PRO_PAGES:
            assert can_access(key) is False

    def test_pro_pages_open_for_pro(self):
        _set_tier("pro")
        for key in PRO_PAGES:
            assert can_access(key) is True

    def test_enterprise_pages_require_enterprise(self):
        _set_tier("pro")
        assert can_access("admin") is False
        _set_tier("enterprise")
        assert can_access("admin") is True
        assert can_access("admin_ops") is True

    def test_unknown_page_default_deny(self):
        _set_tier("pro")
        assert can_access("trajectory_simulator") is False
        assert can_access("saturation") is False
        assert can_access("bom_manager") is False
        assert can_access("") is False

    def test_removed_pages_not_in_pro_set(self):
        assert "saturation" not in PRO_PAGES
        assert "bom_manager" not in PRO_PAGES
        assert "manufacturing" not in PRO_PAGES
        assert "supply_chain" not in PRO_PAGES

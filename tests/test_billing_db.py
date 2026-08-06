"""
tests/test_billing_db.py
========================
Stripe webhook persistence + SQLite-backed user upsert tests.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from database.session import (
    get_user_tier,
    reset_engine,
    update_tier_by_stripe_customer,
    upsert_user,
)


@pytest.fixture()
def sqlite_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    reset_engine()
    yield
    reset_engine()


class TestUserPersistence:
    def test_upsert_and_read_tier(self, sqlite_db):
        assert upsert_user(
            "user-1",
            "a@example.com",
            display_name="Ada",
            tier="free",
            stripe_customer_id="cus_123",
        )
        assert get_user_tier("user-1") == "free"
        assert update_tier_by_stripe_customer("cus_123", "pro")
        assert get_user_tier("user-1") == "pro"

    def test_unknown_customer_returns_false(self, sqlite_db):
        assert update_tier_by_stripe_customer("cus_missing", "pro") is False


class TestWebhookPersistence:
    def test_subscription_created_persists_pro(self, sqlite_db, monkeypatch):
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test")
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
        upsert_user("user-2", "b@example.com", tier="free", stripe_customer_id="cus_abc")

        fake_event = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "customer": "cus_abc",
                    "status": "active",
                    "items": {"data": [{"price": {"id": "price_pro"}}]},
                }
            },
        }

        fake_stripe = MagicMock()
        fake_stripe.Webhook.construct_event.return_value = fake_event

        with patch("billing.stripe_billing._stripe", return_value=fake_stripe):
            from billing.stripe_billing import handle_webhook

            result = handle_webhook(b"{}", "sig")
        assert result["handled"] is True
        assert result["persisted"] is True
        assert get_user_tier("user-2") == "pro"

    def test_subscription_deleted_sets_free(self, sqlite_db, monkeypatch):
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test")
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
        upsert_user("user-3", "c@example.com", tier="pro", stripe_customer_id="cus_del")

        fake_event = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"customer": "cus_del", "status": "canceled"}},
        }
        fake_stripe = MagicMock()
        fake_stripe.Webhook.construct_event.return_value = fake_event

        with patch("billing.stripe_billing._stripe", return_value=fake_stripe):
            from billing.stripe_billing import handle_webhook

            result = handle_webhook(b"{}", "sig")
        assert result["persisted"] is True
        assert get_user_tier("user-3") == "free"

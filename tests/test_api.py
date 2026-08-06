"""
tests/test_api.py
=================
FastAPI read-only endpoint smoke tests.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


class TestHealthAndMissiles:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_missiles_list(self):
        r = client.get("/api/missiles")
        assert r.status_code == 200
        body = r.json()
        assert body["count"] >= 10
        assert len(body["missiles"]) == body["count"]

    def test_missiles_filter_country(self):
        r = client.get("/api/missiles", params={"country": "Iran"})
        assert r.status_code == 200
        for m in r.json()["missiles"]:
            assert m["country"].lower() == "iran"

    def test_missile_by_name(self):
        r = client.get("/api/missiles/Fateh-110")
        assert r.status_code == 200
        assert r.json()["name"] == "Fateh-110"

    def test_missile_missing(self):
        r = client.get("/api/missiles/Not-A-Real-Missile")
        assert r.status_code == 404


class TestOtherEndpoints:
    def test_events(self):
        r = client.get("/api/events")
        assert r.status_code == 200
        assert r.json()["count"] >= 4

    def test_treaties(self):
        r = client.get("/api/treaties")
        assert r.status_code == 200
        assert r.json()["count"] == 8
        assert "origin_year" in r.json()["treaties"][0]

    def test_resources(self):
        r = client.get("/api/resources")
        assert r.status_code == 200
        assert r.json()["count"] >= 10


class TestStripeWebhookRoute:
    def test_webhook_requires_signature(self):
        r = client.post("/stripe/webhook", content=b"{}")
        assert r.status_code == 400

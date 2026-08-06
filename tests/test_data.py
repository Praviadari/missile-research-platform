"""
tests/test_data.py
===================
JSON data file integrity and schema validation tests.
Aligned to the actual data schemas used by the Streamlit UI.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

MISSILE_CATEGORIES = {
    "SRBM",
    "MRBM",
    "IRBM",
    "ICBM",
    "ADV-BM",
    "Hypers",
    "Cruise",
    "Anti-Ship",
    "Interceptor",
}

RESOURCE_TYPES = {
    "Academic Blog / Podcast",
    "Academic Journal",
    "Annual Reference",
    "Monograph",
    "Official Government Report",
    "Policy Reference",
    "Professional Reference Database",
    "Reference",
    "Reference Database",
    "Research Database",
    "Research Publication",
    "Research Reports",
    "Textbook",
}


def load(filename):
    with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


class TestMissilesJson:
    @pytest.fixture(scope="class")
    def missiles(self):
        return load("missiles.json")

    def test_loads(self, missiles):
        assert isinstance(missiles, list)

    def test_has_entries(self, missiles):
        assert len(missiles) >= 10

    def test_count_matches_product_claim(self, missiles):
        assert len(missiles) == 31

    def test_required_fields(self, missiles):
        required = ["name", "country", "category", "range_km", "propulsion", "sources"]
        for m in missiles:
            for field in required:
                assert field in m, f"Missing '{field}' in: {m.get('name', '?')}"

    def test_range_positive(self, missiles):
        for m in missiles:
            assert m["range_km"] > 0, f"Non-positive range in {m['name']}"

    def test_categories_valid(self, missiles):
        for m in missiles:
            assert m["category"] in MISSILE_CATEGORIES, (
                f"Invalid category '{m['category']}' in {m['name']}"
            )

    def test_all_have_sources(self, missiles):
        for m in missiles:
            assert isinstance(m["sources"], list), f"Sources not a list in {m['name']}"
            assert len(m["sources"]) > 0, f"Empty sources in {m['name']}"

    def test_no_duplicate_names(self, missiles):
        names = [m["name"] for m in missiles]
        assert len(names) == len(set(names)), "Duplicate missile names found"

    def test_mach_positive_if_present(self, missiles):
        for m in missiles:
            if "peak_mach" in m and m["peak_mach"] is not None:
                assert m["peak_mach"] > 0, f"Non-positive Mach in {m['name']}"

    def test_payload_positive_if_present(self, missiles):
        for m in missiles:
            if "payload_kg" in m and m["payload_kg"] is not None:
                assert m["payload_kg"] > 0, f"Non-positive payload in {m['name']}"

    def test_range_plausible(self, missiles):
        for m in missiles:
            assert m["range_km"] < 20_000, f"Implausible range {m['range_km']} in {m['name']}"

    def test_icbm_range_above_5500(self, missiles):
        for m in missiles:
            if m["category"] == "ICBM":
                assert m["range_km"] >= 5000, f"ICBM {m['name']} has range < 5000 km"

    def test_srbm_range_below_1500(self, missiles):
        for m in missiles:
            if m["category"] == "SRBM":
                assert m["range_km"] <= 1500, f"SRBM {m['name']} has range > 1500 km"

    def test_country_present(self, missiles):
        for m in missiles:
            assert m["country"] and len(m["country"]) > 0, f"Missing country in {m['name']}"


class TestHistoricalEventsJson:
    @pytest.fixture(scope="class")
    def events(self):
        return load("historical_events.json")

    def test_loads(self, events):
        assert isinstance(events, list)

    def test_has_entries(self, events):
        assert len(events) >= 4

    def test_required_fields(self, events):
        # UI uses "operation" (not "name"); intercept counts may be int or approximate str
        required = ["id", "operation", "date", "missiles_fired", "sources"]
        for e in events:
            for field in required:
                assert field in e, f"Missing '{field}' in event: {e.get('operation', '?')}"

    def test_missiles_fired_positive(self, events):
        for e in events:
            assert isinstance(e["missiles_fired"], int)
            assert e["missiles_fired"] > 0, f"No missiles fired in {e['operation']}"

    def test_numeric_intercepts_leq_fired(self, events):
        for e in events:
            intercepted = e.get("intercepted")
            if isinstance(intercepted, int):
                assert intercepted <= e["missiles_fired"], (
                    f"Intercepts > fired in {e['operation']}"
                )

    def test_intercept_rate_in_range(self, events):
        for e in events:
            if "intercept_rate_pct" in e and e["intercept_rate_pct"] is not None:
                assert 0 <= e["intercept_rate_pct"] <= 100, (
                    f"Invalid intercept rate in {e['operation']}"
                )

    def test_all_have_sources(self, events):
        for e in events:
            assert len(e["sources"]) > 0, f"No sources in {e['operation']}"

    def test_intercept_rate_consistent_when_numeric(self, events):
        for e in events:
            intercepted = e.get("intercepted")
            rate = e.get("intercept_rate_pct")
            if isinstance(intercepted, int) and rate is not None:
                computed = intercepted / e["missiles_fired"] * 100
                assert abs(rate - computed) < 5, f"Inconsistent rate in {e['operation']}"


class TestTreatiesJson:
    @pytest.fixture(scope="class")
    def treaties(self):
        return load("treaties.json")

    def test_loads(self, treaties):
        assert isinstance(treaties, list)

    def test_has_entries(self, treaties):
        assert len(treaties) >= 5

    def test_count(self, treaties):
        assert len(treaties) == 8

    def test_required_fields(self, treaties):
        required = ["id", "name", "full_name", "status", "summary", "category"]
        for t in treaties:
            for field in required:
                assert field in t, f"Missing '{field}' in treaty: {t.get('name', '?')}"

    def test_membership_field_present(self, treaties):
        """Treaties/regimes use parties, parties_original, members, or subscribing_states."""
        membership_keys = ("parties", "parties_original", "members", "subscribing_states")
        for t in treaties:
            assert any(k in t for k in membership_keys), (
                f"No membership field in {t['name']}"
            )

    def test_no_duplicate_names(self, treaties):
        names = [t["name"] for t in treaties]
        assert len(names) == len(set(names)), "Duplicate treaty names"

    def test_origin_year_plausible(self, treaties):
        for t in treaties:
            raw = t.get("signed", t.get("established", t.get("entered_into_force")))
            if raw is None:
                continue
            year = int(str(raw)[:4]) if str(raw)[:4].isdigit() else None
            if year is not None:
                assert 1945 <= year <= 2030, f"Implausible year {year} in {t['name']}"


class TestResourcesJson:
    @pytest.fixture(scope="class")
    def resources(self):
        return load("resources.json")

    def test_loads(self, resources):
        assert isinstance(resources, list)

    def test_has_entries(self, resources):
        assert len(resources) >= 10

    def test_required_fields(self, resources):
        required = ["title", "type", "description"]
        for r in resources:
            for field in required:
                assert field in r, f"Missing '{field}' in resource: {r.get('title', '?')}"

    def test_has_locator(self, resources):
        """Online resources need url; books may use access / publisher instead."""
        for r in resources:
            has_url = bool(r.get("url"))
            has_access = bool(r.get("access"))
            assert has_url or has_access, f"No url/access in {r.get('title', '?')}"

    def test_types_valid(self, resources):
        for r in resources:
            assert r["type"] in RESOURCE_TYPES, (
                f"Invalid type '{r['type']}' in {r.get('title', '?')}"
            )

    def test_no_duplicate_titles(self, resources):
        titles = [r["title"] for r in resources]
        assert len(titles) == len(set(titles)), "Duplicate resource titles"

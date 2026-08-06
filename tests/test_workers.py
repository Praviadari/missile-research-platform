"""
tests/test_workers.py
=====================
Celery task functions execute synchronously (no broker required).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workers.celery_app import export_csv, generate_pdf_report


class TestWorkers:
    def test_export_csv_missiles(self):
        result = export_csv.run("user1234abcd", "missiles", {"country": "Iran"})
        assert result["rows"] > 0
        assert result["filename"].endswith(".csv")
        assert os.path.exists(result["path"])

    def test_pdf_missile_comparison(self):
        result = generate_pdf_report.run(
            "user1234abcd", "missile_comparison", {"country": "Iran"}
        )
        assert result["status"] == "complete"
        assert result["filename"].endswith(".pdf")
        assert os.path.exists(result["path"])
        assert os.path.getsize(result["path"]) > 500

    def test_pdf_unknown_type(self):
        result = generate_pdf_report.run("user1234abcd", "attack_plan", {})
        assert result["status"] == "not_implemented"

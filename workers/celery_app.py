"""
workers/celery_app.py
======================
Celery task queue for async exports and reports.

Run a worker:
    celery -A workers.celery_app worker --loglevel=info --concurrency=2
"""

from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "missile_platform",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    task_soft_time_limit=120,
    task_time_limit=180,
)


def _data_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "data")


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def generate_pdf_report(self, user_id: str, report_type: str, params: dict):
    """
    Generate a PDF report from public JSON data.

    Supported report_type:
      - missile_comparison (default)
      - treaty_brief
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        import json
        import tempfile

        report_type = report_type or "missile_comparison"
        params = params or {}
        styles = getSampleStyleSheet()
        story = []

        if report_type == "missile_comparison":
            path = os.path.join(_data_dir(), "missiles.json")
            with open(path, encoding="utf-8") as f:
                missiles = json.load(f)
            country = (params.get("country") or "").lower()
            category = (params.get("category") or "").lower()
            if country:
                missiles = [
                    m for m in missiles if m.get("country", "").lower() == country
                ]
            if category:
                missiles = [
                    m for m in missiles if m.get("category", "").lower() == category
                ]
            missiles = missiles[:25]
            story.append(Paragraph("Missile Comparison Report", styles["Title"]))
            story.append(Spacer(1, 12))
            story.append(
                Paragraph(
                    f"Entries: {len(missiles)} · Generated for research use from public data.",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 12))
            for m in missiles:
                src_labels = []
                for s in m.get("sources", []):
                    if isinstance(s, dict):
                        src_labels.append(s.get("label", ""))
                    else:
                        src_labels.append(str(s))
                line = (
                    f"<b>{m.get('name','?')}</b> — {m.get('country','?')} / "
                    f"{m.get('category','?')} · range {m.get('range_km','?')} km · "
                    f"propulsion {m.get('propulsion','?')}<br/>"
                    f"Sources: {'; '.join(src_labels) or '—'}"
                )
                story.append(Paragraph(line, styles["BodyText"]))
                story.append(Spacer(1, 8))

        elif report_type == "treaty_brief":
            path = os.path.join(_data_dir(), "treaties.json")
            with open(path, encoding="utf-8") as f:
                treaties = json.load(f)
            story.append(Paragraph("Treaty Brief", styles["Title"]))
            story.append(Spacer(1, 12))
            for t in treaties:
                line = (
                    f"<b>{t.get('name','?')}</b> ({t.get('origin_year','?')}) — "
                    f"status {t.get('status','?')} · members {t.get('member_count','?')}<br/>"
                    f"{t.get('summary','')[:400]}"
                )
                story.append(Paragraph(line, styles["BodyText"]))
                story.append(Spacer(1, 8))
        else:
            return {
                "status": "not_implemented",
                "error": f"PDF report type '{report_type}' is not implemented",
                "user_id": user_id,
            }

        filename = f"{report_type}_{user_id[:8]}.pdf"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            doc = SimpleDocTemplate(tmp.name, pagesize=A4)
            doc.build(story)
            return {
                "status": "complete",
                "filename": filename,
                "path": tmp.name,
                "rows": len(story),
            }
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=2)
def export_csv(self, user_id: str, data_type: str, filters: dict):
    """Export filtered data as CSV."""
    import csv
    import json
    import tempfile

    try:
        file_map = {
            "missiles": "missiles.json",
            "events": "historical_events.json",
            "treaties": "treaties.json",
        }
        source_file = file_map.get(data_type)
        if not source_file:
            return {"error": f"Unknown data_type: {data_type}"}

        with open(os.path.join(_data_dir(), source_file), encoding="utf-8") as f:
            rows = json.load(f)

        filters = filters or {}
        country = filters.get("country")
        category = filters.get("category")
        if country:
            rows = [r for r in rows if r.get("country", "").lower() == country.lower()]
        if category:
            rows = [r for r in rows if r.get("category", "").lower() == category.lower()]

        if not rows:
            return {"rows": 0, "filename": "empty.csv"}

        filename = f"{data_type}_{user_id[:8]}.csv"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as tmp:
            # Flatten nested sources for CSV friendliness
            flat = []
            for r in rows:
                item = dict(r)
                if isinstance(item.get("sources"), list):
                    labels = []
                    for s in item["sources"]:
                        labels.append(s.get("label", str(s)) if isinstance(s, dict) else str(s))
                    item["sources"] = "; ".join(labels)
                flat.append(item)
            fieldnames = sorted({k for row in flat for k in row.keys()})
            writer = csv.DictWriter(tmp, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(flat)
            return {"rows": len(flat), "filename": filename, "path": tmp.name}
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task
def send_notification_email(to_email: str, subject: str, body_html: str):
    """Send a transactional email when SMTP_HOST is configured."""
    smtp_host = os.getenv("SMTP_HOST", "")
    if not smtp_host:
        import logging

        logging.getLogger(__name__).info(
            "Email [dev stub]: to=%s subject=%s", to_email, subject
        )
        return {"sent": False, "reason": "SMTP_HOST not configured"}

    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_FROM", "noreply@localhost")
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", "587"))) as server:
        server.starttls()
        user = os.getenv("SMTP_USER", "")
        password = os.getenv("SMTP_PASSWORD", "")
        if user:
            server.login(user, password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
    return {"sent": True}

"""
workers/celery_app.py
======================
Celery task queue configuration for the Missile Research Platform.

Used for async tasks that are too slow for the Streamlit request cycle:
  - PDF report generation
  - Batch data export (CSV/XLSX)
  - Email delivery
  - Cache warming

Run a worker:
    celery -A workers.celery_app worker --loglevel=info --concurrency=2

Monitor tasks (Flower):
    celery -A workers.celery_app flower --port=5555
"""

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "missile_platform",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

app.conf.update(
    task_serializer         = "json",
    result_serializer       = "json",
    accept_content          = ["json"],
    timezone                = "UTC",
    enable_utc              = True,
    task_track_started      = True,
    task_acks_late          = True,           # re-queue on worker crash
    worker_prefetch_multiplier = 1,           # fairness for long tasks
    result_expires          = 3600,           # results expire after 1 hour
    task_soft_time_limit    = 120,            # warn after 2 min
    task_time_limit         = 180,            # kill after 3 min
)

# ── Task definitions ──────────────────────────────────────────────────────────

@app.task(bind=True, max_retries=3, default_retry_delay=10)
def generate_pdf_report(self, user_id: str, report_type: str, params: dict):
    """
    Generate a PDF report and store in object storage.

    report_type: "missile_comparison" | "historical_analysis" | "treaty_brief"
    params:      filter/customisation parameters for the report

    Returns: {"url": "...", "filename": "..."}
    """
    try:
        # Import here to avoid loading heavy deps in main process
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate
        import tempfile, json

        filename = f"{report_type}_{user_id[:8]}.pdf"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            doc = SimpleDocTemplate(tmp.name, pagesize=A4)
            # TODO: Build report content from params using reportlab
            doc.build([])  # placeholder
            return {"filename": filename, "path": tmp.name, "status": "complete"}

    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=2)
def export_csv(self, user_id: str, data_type: str, filters: dict):
    """
    Export filtered data as CSV.

    data_type: "missiles" | "events" | "treaties"
    Returns: {"rows": int, "filename": str, "path": str}
    """
    import json, csv, tempfile, os

    try:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        file_map = {
            "missiles": "missiles.json",
            "events":   "historical_events.json",
            "treaties": "treaties.json",
        }
        source_file = file_map.get(data_type)
        if not source_file:
            return {"error": f"Unknown data_type: {data_type}"}

        with open(os.path.join(data_dir, source_file)) as f:
            rows = json.load(f)

        # Apply basic filters
        country = filters.get("country")
        category = filters.get("category")
        if country:
            rows = [r for r in rows if r.get("country","").lower() == country.lower()]
        if category:
            rows = [r for r in rows if r.get("category","").lower() == category.lower()]

        if not rows:
            return {"rows": 0, "filename": "empty.csv"}

        filename = f"{data_type}_{user_id[:8]}.csv"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False,
                                         newline="") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            return {"rows": len(rows), "filename": filename, "path": tmp.name}

    except Exception as exc:
        raise self.retry(exc=exc)


@app.task
def send_notification_email(to_email: str, subject: str, body_html: str):
    """
    Send a transactional email. Stub — configure SMTP or SendGrid.

    Used for: welcome emails, upgrade confirmation, export ready notifications.
    """
    smtp_host = os.getenv("SMTP_HOST", "")
    if not smtp_host:
        import logging
        logging.getLogger(__name__).info(
            "Email [dev stub]: to=%s subject=%s", to_email, subject
        )
        return {"sent": False, "reason": "SMTP_HOST not configured"}

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = os.getenv("SMTP_FROM", "noreply@example.com")
    msg["To"]      = to_email
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", "587"))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER",""), os.getenv("SMTP_PASSWORD",""))
        server.send_message(msg)

    return {"sent": True}

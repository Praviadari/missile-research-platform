"""
monitoring/health.py
====================
Health-check and observability utilities for the Missile Research Platform.

Provides:
  - /health FastAPI endpoint handler (see api/main.py)
  - Sentry error-tracking initialisation
  - Structured logging setup
  - Basic uptime / dependency checks

USAGE
-----
    # In app.py startup:
    from monitoring.health import init_monitoring
    init_monitoring()

    # In FastAPI:
    from monitoring.health import health_check
    @app.get("/health")
    async def health(): return await health_check()
"""

import os
import time
import logging
import logging.config

logger = logging.getLogger(__name__)

SENTRY_DSN   = os.getenv("SENTRY_DSN", "")
ENVIRONMENT  = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO").upper()

_START_TIME = time.time()


# ── Logging setup ─────────────────────────────────────────────────────────────

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "logging.Formatter",
            "fmt": '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}',
        },
        "readable": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "readable" if ENVIRONMENT == "development" else "json",
            "stream":    "ext://sys.stdout",
        },
    },
    "root": {
        "level":    LOG_LEVEL,
        "handlers": ["console"],
    },
}


def init_monitoring() -> None:
    """
    Initialise Sentry error tracking and structured logging.
    Call once at application startup.
    """
    logging.config.dictConfig(LOGGING_CONFIG)

    if SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                environment=ENVIRONMENT,
                traces_sample_rate=0.1,     # 10% of transactions
                profiles_sample_rate=0.05,
            )
            logger.info("Sentry initialised (env=%s)", ENVIRONMENT)
        except ImportError:
            logger.warning("sentry-sdk not installed — error tracking disabled")
    else:
        logger.debug("SENTRY_DSN not set — error tracking skipped")


# ── Dependency checks ─────────────────────────────────────────────────────────

def _check_database() -> dict:
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        return {"status": "skipped", "reason": "DATABASE_URL not set"}
    try:
        import sqlalchemy
        engine = sqlalchemy.create_engine(db_url, pool_timeout=3)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "reason": str(e)[:200]}


def _check_redis() -> dict:
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return {"status": "skipped", "reason": "REDIS_URL not set"}
    try:
        import redis
        r = redis.from_url(redis_url, socket_timeout=2)
        r.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "reason": str(e)[:200]}


def _check_data_files() -> dict:
    """Verify all static JSON data files are readable."""
    import json
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    files = ["missiles.json", "historical_events.json", "treaties.json", "resources.json"]
    missing = []
    for f in files:
        path = os.path.join(data_dir, f)
        try:
            with open(path) as fh:
                json.load(fh)
        except Exception as e:
            missing.append(f"{f}: {e}")
    if missing:
        return {"status": "error", "missing": missing}
    return {"status": "ok", "files": len(files)}


async def health_check() -> dict:
    """
    Async health check handler for FastAPI GET /health.
    Returns a structured dict with dependency statuses.
    """
    uptime_s = time.time() - _START_TIME
    result = {
        "status":    "ok",
        "version":   "2.0.0",
        "uptime_s":  round(uptime_s, 1),
        "environment": ENVIRONMENT,
        "checks": {
            "data_files": _check_data_files(),
            "database":   _check_database(),
            "redis":      _check_redis(),
        },
    }

    # Degrade overall status if any critical check fails
    critical = ["data_files", "database"]
    for check_name in critical:
        if result["checks"][check_name].get("status") == "error":
            result["status"] = "degraded"
            break

    return result

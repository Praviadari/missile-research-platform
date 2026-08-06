"""
database/session.py
===================
SQLAlchemy engine/session helpers and user tier persistence.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base, User, UserTier

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://missile:devpassword@localhost:5432/missile_platform",
    )


def get_engine(echo: bool = False):
    global _engine, _SessionLocal
    if _engine is None:
        url = database_url()
        kwargs = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(url, echo=echo, **kwargs)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def reset_engine() -> None:
    """Test helper — drop cached engine."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


@contextmanager
def session_scope() -> Iterator[Session]:
    get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_schema() -> None:
    """Create tables if missing (dev/sqlite). Prefer alembic in production."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def _tier_enum(tier: str) -> UserTier:
    try:
        return UserTier(tier)
    except ValueError:
        return UserTier.free


def upsert_user(
    user_id: str,
    email: str,
    *,
    display_name: Optional[str] = None,
    tier: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
) -> bool:
    """Insert or update a user row. Returns False if DATABASE_URL unavailable."""
    if not user_id or not email:
        return False
    if not os.getenv("DATABASE_URL"):
        return False
    try:
        ensure_schema()
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                user = User(
                    id=user_id,
                    email=email,
                    display_name=display_name or email.split("@")[0],
                    tier=_tier_enum(tier or "free"),
                    stripe_customer_id=stripe_customer_id,
                    created_at=_utcnow(),
                    last_login=_utcnow(),
                )
                session.add(user)
            else:
                user.email = email or user.email
                if display_name:
                    user.display_name = display_name
                if tier is not None:
                    user.tier = _tier_enum(tier)
                if stripe_customer_id:
                    user.stripe_customer_id = stripe_customer_id
                user.last_login = _utcnow()
        return True
    except Exception as e:
        logger.warning("upsert_user failed: %s", e)
        return False


def update_tier_by_stripe_customer(customer_id: str, tier: str) -> bool:
    """Set tier for the user bound to a Stripe customer id."""
    if not customer_id or not os.getenv("DATABASE_URL"):
        return False
    try:
        ensure_schema()
        with session_scope() as session:
            user = (
                session.query(User)
                .filter(User.stripe_customer_id == customer_id)
                .one_or_none()
            )
            if user is None:
                logger.info(
                    "No user for stripe customer %s — tier %s not persisted",
                    customer_id,
                    tier,
                )
                return False
            user.tier = _tier_enum(tier)
        return True
    except Exception as e:
        logger.warning("update_tier_by_stripe_customer failed: %s", e)
        return False


def get_user_tier(user_id: str) -> Optional[str]:
    if not user_id or not os.getenv("DATABASE_URL"):
        return None
    try:
        ensure_schema()
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return None
            return user.tier.value if hasattr(user.tier, "value") else str(user.tier)
    except Exception as e:
        logger.warning("get_user_tier failed: %s", e)
        return None


def tier_counts() -> dict[str, int]:
    """Return {tier: count} for admin dashboard; empty if DB unavailable."""
    if not os.getenv("DATABASE_URL"):
        return {}
    try:
        ensure_schema()
        with session_scope() as session:
            rows = session.query(User.tier).all()
            counts: dict[str, int] = {}
            for (tier,) in rows:
                key = tier.value if hasattr(tier, "value") else str(tier)
                counts[key] = counts.get(key, 0) + 1
            return counts
    except Exception as e:
        logger.warning("tier_counts failed: %s", e)
        return {}

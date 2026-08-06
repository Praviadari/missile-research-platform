"""
database/models.py
==================
SQLAlchemy ORM models for the Missile Analysis & Research Platform.
"""

from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    JSON, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class UserTier(str, enum.Enum):
    anon       = "anon"
    free       = "free"
    pro        = "pro"
    enterprise = "enterprise"


class User(Base):
    __tablename__ = "users"

    id           = Column(String(64),  primary_key=True)   # Supabase UUID
    email        = Column(String(256), unique=True, nullable=False)
    display_name = Column(String(128))
    tier         = Column(Enum(UserTier), default=UserTier.free, nullable=False)
    stripe_customer_id = Column(String(64))
    created_at   = Column(DateTime, default=datetime.utcnow)
    last_login   = Column(DateTime)

    saved_searches = relationship("SavedSearch", back_populates="user")
    notes          = relationship("ResearchNote", back_populates="user")


class SavedSearch(Base):
    """User-saved missile database filters / search presets."""
    __tablename__ = "saved_searches"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String(64), ForeignKey("users.id"), nullable=False)
    name       = Column(String(128), nullable=False)
    filters    = Column(JSON)   # serialised filter state
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_searches")


class ResearchNote(Base):
    """User annotations on missile entries or events."""
    __tablename__ = "research_notes"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(String(64), ForeignKey("users.id"), nullable=False)
    subject_id  = Column(String(128))   # missile name or event id
    subject_type = Column(String(32))   # "missile" | "event" | "treaty"
    note_text   = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="notes")


class AnalyticsEvent(Base):
    """Page-view and feature-use analytics (privacy-preserving)."""
    __tablename__ = "analytics_events"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String(64), nullable=True)   # nullable for anon
    event_name = Column(String(128), nullable=False)
    page       = Column(String(64))
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

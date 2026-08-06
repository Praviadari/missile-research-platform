"""Initial schema for users, saved searches, notes, analytics.

Revision ID: 001_initial
Revises:
Create Date: 2026-08-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=256), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=128)),
        sa.Column(
            "tier",
            sa.Enum("anon", "free", "pro", "enterprise", name="usertier"),
            nullable=False,
            server_default="free",
        ),
        sa.Column("stripe_customer_id", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("last_login", sa.DateTime()),
    )
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("filters", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "research_notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("subject_id", sa.String(length=128)),
        sa.Column("subject_type", sa.String(length=32)),
        sa.Column("note_text", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("event_name", sa.String(length=128), nullable=False),
        sa.Column("page", sa.String(length=64)),
        sa.Column("properties", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("research_notes")
    op.drop_table("saved_searches")
    op.drop_table("users")
    sa.Enum(name="usertier").drop(op.get_bind(), checkfirst=True)

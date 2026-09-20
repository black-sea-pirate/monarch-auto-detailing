"""Add the protected admin inbox and durable notification metadata.

Revision ID: 20260920_0002
Revises: 20260917_0001
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260920_0002"
down_revision = "20260917_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quote_requests",
        sa.Column("contact_method", sa.String(length=30), server_default="other", nullable=False),
    )
    op.add_column(
        "quote_requests",
        sa.Column(
            "requested_services",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "quote_requests",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "quote_requests", sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "quote_requests", sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "quote_requests", sa.Column("purge_after", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_quote_requests_purge_after", "quote_requests", ["purge_after"])

    op.add_column(
        "quote_request_deliveries",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "quote_request_deliveries",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_quote_request_deliveries_next_attempt_at",
        "quote_request_deliveries",
        ["next_attempt_at"],
    )

    op.create_table(
        "admin_audit_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("admin_email", sa.String(length=320), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_audit_events_action", "admin_audit_events", ["action"])
    op.create_index("ix_admin_audit_events_quote_id", "admin_audit_events", ["quote_id"])
    op.create_index("ix_admin_audit_events_created_at", "admin_audit_events", ["created_at"])

    op.execute(
        """
        UPDATE quote_requests
        SET status = CASE
            WHEN status = 'uploading' THEN 'uploading'
            WHEN status IN ('accepted_purged', 'expired_purged') THEN status
            ELSE 'new'
        END
        """
    )
    op.execute(
        """
        UPDATE quote_request_deliveries
        SET next_attempt_at = now()
        WHERE delivered_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_events_created_at", table_name="admin_audit_events")
    op.drop_index("ix_admin_audit_events_quote_id", table_name="admin_audit_events")
    op.drop_index("ix_admin_audit_events_action", table_name="admin_audit_events")
    op.drop_table("admin_audit_events")
    op.drop_index(
        "ix_quote_request_deliveries_next_attempt_at",
        table_name="quote_request_deliveries",
    )
    op.drop_column("quote_request_deliveries", "next_attempt_at")
    op.drop_column("quote_request_deliveries", "last_attempt_at")
    op.drop_index("ix_quote_requests_purge_after", table_name="quote_requests")
    op.drop_column("quote_requests", "purge_after")
    op.drop_column("quote_requests", "accepted_at")
    op.drop_column("quote_requests", "viewed_at")
    op.drop_column("quote_requests", "updated_at")
    op.drop_column("quote_requests", "requested_services")
    op.drop_column("quote_requests", "contact_method")

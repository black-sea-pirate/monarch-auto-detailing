"""Create the original quote intake schema.

Revision ID: 20260917_0001
Revises:
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260917_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quote_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("contact", sa.String(length=200), nullable=False),
        sa.Column("vehicle", sa.String(length=160), nullable=False),
        sa.Column("community", sa.String(length=120), nullable=False),
        sa.Column("concern", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("upload_token_hash", sa.String(length=64), nullable=False),
        sa.Column("photo_count", sa.Integer(), nullable=False),
        sa.Column("video_count", sa.Integer(), nullable=False),
        sa.Column("upload_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_requests_created_at", "quote_requests", ["created_at"])
    op.create_index("ix_quote_requests_status", "quote_requests", ["status"])

    op.create_table(
        "quote_request_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["quote_id"], ["quote_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_name"),
    )
    op.create_index("ix_quote_request_uploads_quote_id", "quote_request_uploads", ["quote_id"])

    op.create_table(
        "quote_request_deliveries",
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_chat_id", sa.String(length=100), nullable=True),
        sa.Column("summary_message_id", sa.BigInteger(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purged_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["quote_id"], ["quote_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("quote_id"),
    )


def downgrade() -> None:
    op.drop_table("quote_request_deliveries")
    op.drop_index("ix_quote_request_uploads_quote_id", table_name="quote_request_uploads")
    op.drop_table("quote_request_uploads")
    op.drop_index("ix_quote_requests_status", table_name="quote_requests")
    op.drop_index("ix_quote_requests_created_at", table_name="quote_requests")
    op.drop_table("quote_requests")

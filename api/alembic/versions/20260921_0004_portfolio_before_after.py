"""Add optional after photos to portfolio work.

Revision ID: 20260921_0004
Revises: 20260921_0003
"""

import sqlalchemy as sa

from alembic import op

revision = "20260921_0004"
down_revision = "20260921_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portfolio_images",
        sa.Column("after_original_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "portfolio_images",
        sa.Column("after_stored_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "portfolio_images",
        sa.Column("after_content_type", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "portfolio_images",
        sa.Column("after_size_bytes", sa.BigInteger(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_portfolio_images_after_stored_name",
        "portfolio_images",
        ["after_stored_name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_portfolio_images_after_stored_name",
        "portfolio_images",
        type_="unique",
    )
    op.drop_column("portfolio_images", "after_size_bytes")
    op.drop_column("portfolio_images", "after_content_type")
    op.drop_column("portfolio_images", "after_stored_name")
    op.drop_column("portfolio_images", "after_original_name")

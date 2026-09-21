"""Add editable site settings and portfolio images.

Revision ID: 20260921_0003
Revises: 20260920_0002
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260921_0003"
down_revision = "20260920_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "site_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pricing", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sections", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.String(length=320), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("id = 1", name="ck_site_settings_singleton"),
    )
    op.create_table(
        "portfolio_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("caption", sa.String(length=240), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_name"),
    )
    op.create_index("ix_portfolio_images_sort_order", "portfolio_images", ["sort_order"])
    op.create_index("ix_portfolio_images_is_enabled", "portfolio_images", ["is_enabled"])

    op.execute(
        """
        INSERT INTO site_settings (id, pricing, sections, version)
        VALUES (
            1,
            '{
              "maintenance": {"base_price_cents": 9900, "discount_price_cents": null, "discount_enabled": false},
              "deep": {"base_price_cents": 17900, "discount_price_cents": null, "discount_enabled": false},
              "complete": {"base_price_cents": 24900, "discount_price_cents": null, "discount_enabled": false},
              "pet_hair": {"base_price_cents": 4500, "discount_price_cents": null, "discount_enabled": false},
              "extraction": {"base_price_cents": 2500, "discount_price_cents": null, "discount_enabled": false},
              "leather": {"base_price_cents": 3000, "discount_price_cents": null, "discount_enabled": false},
              "salt_stain": {"base_price_cents": 3000, "discount_price_cents": null, "discount_enabled": false},
              "suv_surcharge": {"base_price_cents": 2500, "discount_price_cents": null, "discount_enabled": false},
              "large_vehicle_surcharge": {"base_price_cents": 5000, "discount_price_cents": null, "discount_enabled": false}
            }'::jsonb,
            '{"pricing_enabled": true, "portfolio_enabled": false, "founding_offer_enabled": false}'::jsonb,
            1
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_portfolio_images_is_enabled", table_name="portfolio_images")
    op.drop_index("ix_portfolio_images_sort_order", table_name="portfolio_images")
    op.drop_table("portfolio_images")
    op.drop_table("site_settings")

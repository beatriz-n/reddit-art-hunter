"""Add artwork profile, classifications, and commission services."""

import sqlalchemy as sa
from alembic import op

revision = "0002_art_profile"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "art_styles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False, unique=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.CheckConstraint("kind IN ('style', 'category', 'theme')", name="ck_art_styles_kind"),
    )
    op.create_table(
        "artworks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=80), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(length=40), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "artwork_styles",
        sa.Column(
            "artwork_id",
            sa.String(length=36),
            sa.ForeignKey("artworks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "style_id",
            sa.Integer(),
            sa.ForeignKey("art_styles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "commission_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("price_min", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_max", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("price_min >= 0", name="ck_commission_services_price_min_nonnegative"),
        sa.CheckConstraint("price_max >= 0", name="ck_commission_services_price_max_nonnegative"),
        sa.CheckConstraint("price_max >= price_min", name="ck_commission_services_price_order"),
    )


def downgrade() -> None:
    op.drop_table("commission_services")
    op.drop_table("artwork_styles")
    op.drop_table("artworks")
    op.drop_table("art_styles")

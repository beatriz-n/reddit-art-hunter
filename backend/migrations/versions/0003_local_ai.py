"""Add persisted structured analysis of local portfolio artwork."""

import sqlalchemy as sa
from alembic import op

revision = "0003_local_ai"
down_revision = "0002_art_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artwork_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artwork_id",
            sa.String(length=36),
            sa.ForeignKey("artworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_artwork_analyses_artwork_id", "artwork_analyses", ["artwork_id"])


def downgrade() -> None:
    op.drop_index("ix_artwork_analyses_artwork_id", table_name="artwork_analyses")
    op.drop_table("artwork_analyses")

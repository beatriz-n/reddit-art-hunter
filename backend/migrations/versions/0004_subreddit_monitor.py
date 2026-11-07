"""Add subreddit monitoring configuration, posts and search history."""

import sqlalchemy as sa
from alembic import op

revision = "0004_subreddit_monitor"
down_revision = "0003_local_ai"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subreddits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("poll_interval_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_posts_per_check", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("include_keywords", sa.JSON(), nullable=False),
        sa.Column("exclude_keywords", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("poll_interval_minutes >= 15", name="ck_subreddits_poll_interval"),
    )
    op.create_index("ix_subreddits_name", "subreddits", ["name"], unique=True)
    op.create_table(
        "monitored_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reddit_id", sa.String(length=16), nullable=False),
        sa.Column(
            "subreddit_id",
            sa.Integer(),
            sa.ForeignKey("subreddits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("permalink", sa.String(length=500), nullable=False),
        sa.Column("created_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_monitored_posts_reddit_id", "monitored_posts", ["reddit_id"], unique=True)
    op.create_index("ix_monitored_posts_subreddit_id", "monitored_posts", ["subreddit_id"])
    op.create_table(
        "search_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "subreddit_id",
            sa.Integer(),
            sa.ForeignKey("subreddits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("posts_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("posts_matched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_search_runs_subreddit_id", "search_runs", ["subreddit_id"])


def downgrade() -> None:
    op.drop_index("ix_search_runs_subreddit_id", table_name="search_runs")
    op.drop_table("search_runs")
    op.drop_index("ix_monitored_posts_subreddit_id", table_name="monitored_posts")
    op.drop_index("ix_monitored_posts_reddit_id", table_name="monitored_posts")
    op.drop_table("monitored_posts")
    op.drop_index("ix_subreddits_name", table_name="subreddits")
    op.drop_table("subreddits")

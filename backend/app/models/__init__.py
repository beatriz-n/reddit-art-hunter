from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

artwork_styles = Table(
    "artwork_styles",
    Base.metadata,
    Column(
        "artwork_id", String(36), ForeignKey("artworks.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("style_id", ForeignKey("art_styles.id", ondelete="CASCADE"), primary_key=True),
)


class Artwork(Base):
    __tablename__ = "artworks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(40), nullable=False)
    byte_size: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    styles: Mapped[list["ArtStyle"]] = relationship(
        secondary=artwork_styles, back_populates="artworks"
    )


class ArtStyle(Base):
    __tablename__ = "art_styles"
    __table_args__ = (
        CheckConstraint("kind IN ('style', 'category', 'theme')", name="ck_art_styles_kind"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    artworks: Mapped[list[Artwork]] = relationship(
        secondary=artwork_styles, back_populates="styles"
    )


class CommissionService(Base):
    __tablename__ = "commission_services"
    __table_args__ = (
        CheckConstraint("price_min >= 0", name="ck_commission_services_price_min_nonnegative"),
        CheckConstraint("price_max >= 0", name="ck_commission_services_price_max_nonnegative"),
        CheckConstraint("price_max >= price_min", name="ck_commission_services_price_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    price_min: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_max: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ArtworkAnalysis(Base):
    __tablename__ = "artwork_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artworks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    artwork: Mapped[Artwork] = relationship()


class Subreddit(Base):
    __tablename__ = "subreddits"
    __table_args__ = (
        CheckConstraint("poll_interval_minutes >= 15", name="ck_subreddits_poll_interval"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    poll_interval_minutes: Mapped[int] = mapped_column(default=60, nullable=False)
    max_posts_per_check: Mapped[int] = mapped_column(default=25, nullable=False)
    include_keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    exclude_keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MonitoredPost(Base):
    __tablename__ = "monitored_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    reddit_id: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    subreddit_id: Mapped[int] = mapped_column(
        ForeignKey("subreddits.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    permalink: Mapped[str] = mapped_column(String(500), nullable=False)
    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    subreddit: Mapped[Subreddit] = relationship()


class SearchRun(Base):
    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    subreddit_id: Mapped[int] = mapped_column(
        ForeignKey("subreddits.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    posts_fetched: Mapped[int] = mapped_column(default=0, nullable=False)
    posts_matched: Mapped[int] = mapped_column(default=0, nullable=False)
    message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    subreddit: Mapped[Subreddit] = relationship()

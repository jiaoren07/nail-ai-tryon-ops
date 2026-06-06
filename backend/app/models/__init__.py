"""SQLAlchemy ORM models for the 6 application tables.

Schema source: design-docu.md §4.2 (tables) and §4.3 (indexes).
Time fields default to UTC per design-docu §4 时区约定.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Style(Base):
    __tablename__ = "styles"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    gender: Mapped[str]
    cover_url: Mapped[str]
    style_tags: Mapped[str] = mapped_column(Text)
    color_main: Mapped[str]
    color_tone: Mapped[str]
    length_pref: Mapped[str]
    complexity: Mapped[int]
    heat_score: Mapped[float] = mapped_column(default=50.0)
    is_active: Mapped[int] = mapped_column(default=1)
    display_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class Tryon(Base):
    __tablename__ = "tryons"
    __table_args__ = (
        Index("ix_tryons_style_created", "style_id", "created_at"),
        Index("ix_tryons_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str]
    user_gender: Mapped[str]
    style_id: Mapped[str] = mapped_column(ForeignKey("styles.id"))
    skin_tone: Mapped[str]
    hand_shape: Mapped[str]
    from_module: Mapped[str]
    is_collected: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class StyleStats(Base):
    __tablename__ = "style_stats"
    __table_args__ = (
        UniqueConstraint("style_id", "stat_date", name="uq_style_stats_style_date"),
        Index("ix_style_stats_date_tryons", "stat_date", "tryon_count"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    style_id: Mapped[str] = mapped_column(ForeignKey("styles.id"))
    stat_date: Mapped[date]
    tryon_count: Mapped[int] = mapped_column(default=0)
    collect_count: Mapped[int] = mapped_column(default=0)
    exposure_count: Mapped[int] = mapped_column(default=0)
    click_count: Mapped[int] = mapped_column(default=0)


class OpsAction(Base):
    __tablename__ = "ops_actions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    style_id: Mapped[str] = mapped_column(ForeignKey("styles.id"))
    action_type: Mapped[str]
    reason: Mapped[str | None] = mapped_column(Text, default=None)
    operator: Mapped[str] = mapped_column(default="ai_assistant")
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_type_end", "type", "period_end"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str]
    title: Mapped[str]
    content_md: Mapped[str] = mapped_column(Text)
    period_start: Mapped[date]
    period_end: Mapped[date]
    trigger_source: Mapped[str]
    email_status: Mapped[str] = mapped_column(default="pending")
    email_sent_at: Mapped[datetime | None] = mapped_column(default=None)
    email_error: Mapped[str | None] = mapped_column(Text, default=None)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_unread_recent", "is_read", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str]
    ref_id: Mapped[int | None] = mapped_column(default=None)
    title: Mapped[str]
    summary: Mapped[str] = mapped_column(Text)
    is_read: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    read_at: Mapped[datetime | None] = mapped_column(default=None)


__all__ = [
    "Base",
    "Style",
    "Tryon",
    "StyleStats",
    "OpsAction",
    "Report",
    "Notification",
]

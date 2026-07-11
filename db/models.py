from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Telegram user with monitoring preferences."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    monitoring_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    topics: Mapped[list["UserTopic"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    disabled_sources: Mapped[list["UserDisabledSource"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserTopic(Base):
    """Selected topic for a user."""

    __tablename__ = "user_topics"
    __table_args__ = (UniqueConstraint("user_id", "topic_key", name="uq_user_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_key: Mapped[str] = mapped_column(String(64))

    user: Mapped["User"] = relationship(back_populates="topics")


class UserDisabledSource(Base):
    """Scrape source the user turned OFF.

    Absence of a row means the source is enabled (default). Storing the
    disabled set (rather than enabled) keeps new sources on by default and
    matches the user's mental model: "uncheck a site to stop parsing it".
    """

    __tablename__ = "user_disabled_sources"
    __table_args__ = (UniqueConstraint("user_id", "source_key", name="uq_user_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source_key: Mapped[str] = mapped_column(String(64))

    user: Mapped["User"] = relationship(back_populates="disabled_sources")


class SeenPost(Base):
    """Already processed postings to avoid duplicates."""

    __tablename__ = "seen_posts"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_seen_source_ext"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_topics: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Signals used to rank postings by relevance (top-5 feature).
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    responses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_value: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # True for job vacancies / hiring (найм) — excluded from notifications and
    # from the "Топ-5 актуальных" list (user wants orders, not job offers).
    is_vacancy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ScrapeRun(Base):
    """Log of scrape cycles for stats/debugging."""

    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    posts_found: Mapped[int] = mapped_column(Integer, default=0)
    posts_new: Mapped[int] = mapped_column(Integer, default=0)
    posts_matched: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

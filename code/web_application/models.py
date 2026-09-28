from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="sessions",
    )


class Fixture(Base):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    fixture_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    teams: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    related_items: Mapped[list["FixtureRelatedItem"]] = relationship(
        back_populates="fixture",
        cascade="all, delete-orphan",
    )


class FixtureRelatedItem(Base):
    __tablename__ = "fixture_related_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    fixture: Mapped["Fixture"] = relationship(
        back_populates="related_items",
    )
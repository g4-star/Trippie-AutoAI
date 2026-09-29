from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DiscoveryState(Base):
    """
    Persistent state for autonomous internet job discovery.

    Each user has one state record. The query_offset determines where
    the next discovery cycle starts in the generated search plan.
    """

    __tablename__ = "discovery_states"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        primary_key=True,
    )

    query_offset: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_cycles: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

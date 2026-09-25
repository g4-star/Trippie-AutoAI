from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    agent_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    automatic_job_discovery: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    minimum_match_score: Mapped[int] = mapped_column(
        Integer,
        default=70,
        nullable=False,
    )

    automatic_application: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    daily_application_limit: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    email_monitoring: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    auto_reply: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    require_approval: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

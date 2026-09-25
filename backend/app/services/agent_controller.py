from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settings import Settings


def is_agent_running(
    db: Session,
    user_id: int,
) -> bool:
    settings = db.scalar(
        select(Settings).where(
            Settings.user_id == user_id
        )
    )

    return bool(
        settings
        and settings.agent_enabled
    )


def require_agent_running(
    db: Session,
    user_id: int,
) -> None:
    if not is_agent_running(
        db=db,
        user_id=user_id,
    ):
        raise RuntimeError(
            "AI Agent is stopped. "
            "Automatic processing is disabled."
        )

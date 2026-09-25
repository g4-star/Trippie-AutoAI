from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import Settings


router = APIRouter(
    prefix="/api/agent",
    tags=["AI Agent"],
)


def _get_or_create_settings(
    user_id: int,
    db: Session,
) -> Settings:
    settings = db.scalar(
        select(Settings).where(
            Settings.user_id == user_id
        )
    )

    if settings:
        return settings

    settings = Settings(
        user_id=user_id,
        agent_enabled=False,
        automatic_job_discovery=True,
        minimum_match_score=70,
        automatic_application=False,
        daily_application_limit=10,
        email_monitoring=True,
        auto_reply=False,
        require_approval=True,
    )

    db.add(settings)
    db.commit()
    db.refresh(settings)

    return settings


def _agent_response(settings: Settings) -> dict:
    return {
        "user_id": settings.user_id,
        "running": settings.agent_enabled,
        "status": (
            "running"
            if settings.agent_enabled
            else "stopped"
        ),
        "automatic_job_discovery": (
            settings.automatic_job_discovery
        ),
        "automatic_application": (
            settings.automatic_application
        ),
        "email_monitoring": settings.email_monitoring,
        "auto_reply": settings.auto_reply,
        "require_approval": settings.require_approval,
    }


@router.get("/{user_id}")
def get_agent_status(
    user_id: int,
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(
        user_id,
        db,
    )

    return _agent_response(settings)


@router.post("/{user_id}/run")
def run_agent(
    user_id: int,
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(
        user_id,
        db,
    )

    settings.agent_enabled = True

    db.commit()
    db.refresh(settings)

    return {
        "message": "AI Agent started.",
        "cycle": {
            "status": "scheduled",
            "message": (
                "Background worker will run the next "
                "agent cycle automatically."
            ),
        },
        **_agent_response(settings),
    }


@router.post("/{user_id}/stop")
def stop_agent(
    user_id: int,
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(
        user_id,
        db,
    )

    settings.agent_enabled = False

    db.commit()
    db.refresh(settings)

    return {
        "message": "AI Agent stopped.",
        **_agent_response(settings),
    }

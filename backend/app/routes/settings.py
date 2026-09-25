from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import Settings


router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"],
)


class SettingsResponse(BaseModel):
    user_id: int
    agent_enabled: bool
    automatic_job_discovery: bool
    minimum_match_score: int
    automatic_application: bool
    daily_application_limit: int
    email_monitoring: bool
    auto_reply: bool
    require_approval: bool


class SettingsUpdate(BaseModel):
    agent_enabled: bool | None = None
    automatic_job_discovery: bool | None = None
    minimum_match_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    automatic_application: bool | None = None
    daily_application_limit: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    email_monitoring: bool | None = None
    auto_reply: bool | None = None
    require_approval: bool | None = None


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
        agent_enabled=True,
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


def _response(settings: Settings) -> dict:
    return {
        "user_id": settings.user_id,
        "agent_enabled": settings.agent_enabled,
        "automatic_job_discovery": settings.automatic_job_discovery,
        "minimum_match_score": settings.minimum_match_score,
        "automatic_application": settings.automatic_application,
        "daily_application_limit": settings.daily_application_limit,
        "email_monitoring": settings.email_monitoring,
        "auto_reply": settings.auto_reply,
        "require_approval": settings.require_approval,
    }


@router.get("/{user_id}", response_model=SettingsResponse)
def get_settings(
    user_id: int,
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(
        user_id,
        db,
    )

    return _response(settings)


@router.patch("/{user_id}", response_model=SettingsResponse)
def update_settings(
    user_id: int,
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(
        user_id,
        db,
    )

    updates = payload.model_dump(
        exclude_unset=True
    )

    for field, value in updates.items():
        setattr(settings, field, value)

    # Safety invariant:
    # automatic replies cannot bypass approval unless
    # the user explicitly disables the approval requirement.
    #
    # Even then, the email agent's category-specific rules
    # remain in force.
    db.commit()
    db.refresh(settings)

    return _response(settings)

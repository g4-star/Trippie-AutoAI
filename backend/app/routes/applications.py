from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.services.application_engine import prepare_application


router = APIRouter(
    prefix="/api/applications",
    tags=["Applications"],
)


VALID_STATUSES = {
    "prepared",
    "submitted",
    "under_review",
    "interview",
    "assessment",
    "offer",
    "accepted",
    "rejected",
    "withdrawn",
    "follow_up_required",
    "manual_action_required",
    "submission_failed",
}


class ApplicationStatusUpdate(BaseModel):
    status: str


def application_response(
    application: Application,
    job: Job | None = None,
) -> dict:
    return {
        "id": application.id,
        "user_id": application.user_id,
        "job_id": application.job_id,
        "status": application.status,
        "match_score": application.match_score,
        "cover_letter": application.cover_letter,
        "notes": application.notes,
        "application_url": application.application_url,
        "submitted_at": application.submitted_at,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
        "job": (
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "source": job.source,
                "job_url": job.job_url,
            }
            if job
            else None
        ),
    }


@router.get("/{user_id}")
def get_user_applications(
    user_id: int,
    db: Session = Depends(get_db),
):
    applications = db.scalars(
        select(Application)
        .where(Application.user_id == user_id)
        .order_by(Application.created_at.desc())
    ).all()

    results = []

    for application in applications:
        job = db.get(Job, application.job_id)

        results.append(
            application_response(
                application=application,
                job=job,
            )
        )

    return {
        "count": len(results),
        "applications": results,
    }


@router.get("/{user_id}/{application_id}")
def get_application(
    user_id: int,
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.scalar(
        select(Application)
        .where(
            Application.id == application_id,
            Application.user_id == user_id,
        )
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    job = db.get(Job, application.job_id)

    return application_response(
        application=application,
        job=job,
    )


@router.post("/{user_id}/prepare/{job_id}")
def prepare_application_endpoint(
    user_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    result = prepare_application(
        db=db,
        user_id=user_id,
        job_id=job_id,
    )

    if not result["success"]:
        if result.get("error") == "User not found.":
            raise HTTPException(
                status_code=404,
                detail=result["error"],
            )

        if result.get("error") == "Job not found.":
            raise HTTPException(
                status_code=404,
                detail=result["error"],
            )

        if result.get("application_id"):
            raise HTTPException(
                status_code=409,
                detail=result["error"],
            )

        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Unable to prepare application."),
        )

    return result


@router.put("/{application_id}/status")
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
):
    status = payload.status.strip().lower()

    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid application status.",
                "valid_statuses": sorted(VALID_STATUSES),
            },
        )

    application = db.get(Application, application_id)

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    application.status = status

    if status == "submitted" and application.submitted_at is None:
        application.submitted_at = datetime.utcnow()

    application.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(application)

    job = db.get(Job, application.job_id)

    return application_response(
        application=application,
        job=job,
    )

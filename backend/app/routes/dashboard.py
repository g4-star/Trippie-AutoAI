from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.email import Email
from app.models.job import Job


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("/{user_id}")
def get_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail='Access denied.')

    total_jobs = db.scalar(
        select(func.count(Job.id))
        .where(Job.is_active.is_(True))
    ) or 0

    matching_jobs = db.scalar(
        select(func.count(Job.id))
        .where(
            Job.is_active.is_(True),
            Job.match_score.is_not(None),
            Job.match_score >= 70,
        )
    ) or 0

    applications = db.scalar(
        select(func.count(Application.id))
        .where(Application.user_id == user_id)
    ) or 0

    successfully_applied = db.scalar(
        select(func.count(Application.id))
        .where(
            Application.user_id == user_id,
            Application.status.in_(
                ["submitted", "under_review", "interview", "assessment", "offer", "accepted"]
            ),
        )
    ) or 0

    emails_received = db.scalar(
        select(func.count(Email.id))
        .where(Email.user_id == user_id)
    ) or 0

    return {
        "total_jobs": total_jobs,
        "matching_jobs": matching_jobs,
        "applications": applications,
        "successfully_applied": successfully_applied,
        "emails_received": emails_received,
    }

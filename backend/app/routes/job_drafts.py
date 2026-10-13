from __future__ import annotations

import logging
import os
import secrets

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.job_email_draft import JobEmailDraft
from app.services.gmail_draft_service import (
    complete_draft_authorization,
    get_draft_authorization_url,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/job-drafts", tags=["Job Application Drafts"])
basic_auth = HTTPBasic(auto_error=False)


def require_draft_api_access(
    credentials: HTTPBasicCredentials | None = Depends(basic_auth),
) -> int:
    configured_user = os.getenv("AUTOAI_USER_ID", "1")
    expected_secret = os.getenv("JOB_DRAFTS_API_SECRET", "")

    if not expected_secret:
        logger.error("JOB_DRAFTS_API_SECRET is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Draft API access is not configured.",
        )

    username_ok = (
        credentials is not None
        and secrets.compare_digest(credentials.username, configured_user)
    )
    password_ok = (
        credentials is not None
        and secrets.compare_digest(credentials.password, expected_secret)
    )

    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        return int(configured_user)
    except ValueError as error:
        logger.error("AUTOAI_USER_ID must be an integer")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Draft API configuration is invalid.",
        ) from error


@router.get("/gmail/connect")
def connect_gmail_for_job_drafts(
    request: Request,
    authorized_user_id: int = Depends(require_draft_api_access),
    db: Session = Depends(get_db),
):
    del authorized_user_id
    redirect_uri = str(request.url_for("job_gmail_draft_callback"))

    try:
        authorization_url = get_draft_authorization_url(
            redirect_uri=redirect_uri,
            db=db,
        )
        return RedirectResponse(url=authorization_url, status_code=302)
    except Exception:
        logger.exception("Unable to start Gmail draft authorization")
        raise HTTPException(
            status_code=500,
            detail="Unable to start Gmail draft authorization.",
        ) from None


@router.get("/gmail/callback", name="job_gmail_draft_callback")
def gmail_draft_callback(request: Request, db: Session = Depends(get_db)):
    oauth_error = request.query_params.get("error")
    if oauth_error:
        raise HTTPException(
            status_code=400,
            detail="Gmail authorization was not completed.",
        )

    if not request.query_params.get("code"):
        raise HTTPException(
            status_code=400,
            detail="Gmail authorization code was not provided.",
        )

    try:
        complete_draft_authorization(
            authorization_response=str(request.url),
            state=request.query_params.get("state", ""),
            redirect_uri=str(request.url_for("job_gmail_draft_callback")),
            db=db,
            user_id=int(os.getenv("AUTOAI_USER_ID", "1")),
        )
    except Exception:
        logger.exception("Unable to complete Gmail draft authorization")
        raise HTTPException(
            status_code=400,
            detail="Unable to complete Gmail authorization. Check server logs.",
        ) from None

    return {
        "status": "connected",
        "message": (
            "Gmail is authorized to create job-application drafts. "
            "Review and send each email manually in Gmail."
        ),
    }


@router.get("/{user_id}")
def list_job_application_drafts(
    user_id: int,
    limit: int = 50,
    authorized_user_id: int = Depends(require_draft_api_access),
    db: Session = Depends(get_db),
):
    if user_id != authorized_user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    rows = db.execute(
        select(JobEmailDraft, Job)
        .join(Job, Job.id == JobEmailDraft.job_id)
        .where(JobEmailDraft.user_id == authorized_user_id)
        .order_by(JobEmailDraft.created_at.desc())
        .limit(max(1, min(limit, 100)))
    ).all()

    return {
        "count": len(rows),
        "drafts": [
            {
                "id": draft.id,
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "job_url": job.job_url,
                "recipient_email": draft.recipient_email,
                "subject": draft.subject,
                "body": draft.body,
                "body_html": draft.body_html,
                "match_score": draft.match_score,
                "status": draft.status,
                "gmail_draft_id": draft.gmail_draft_id,
                "gmail_draft_url": draft.gmail_draft_url,
                "notification_sent": draft.notification_sent,
                "notification_error": draft.notification_error,
                "error": draft.error,
                "created_at": draft.created_at,
                "updated_at": draft.updated_at,
            }
            for draft, job in rows
        ],
    }

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.job_email_draft import JobEmailDraft
from app.services.gmail_draft_service import (
    complete_draft_authorization,
    get_draft_authorization_url,
)

router = APIRouter(prefix="/api/job-drafts", tags=["Job Application Drafts"])


@router.get("/gmail/connect")
def connect_gmail_for_job_drafts(request: Request):
    redirect_uri = str(request.url_for("job_gmail_draft_callback"))
    try:
        return RedirectResponse(
            url=get_draft_authorization_url(redirect_uri), status_code=302
        )
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Unable to start Gmail draft authorization: {error}"
        ) from error


@router.get("/gmail/callback", name="job_gmail_draft_callback")
def gmail_draft_callback(request: Request, db: Session = Depends(get_db)):
    error = request.query_params.get("error")
    if error:
        raise HTTPException(status_code=400, detail=f"Gmail authorization failed: {error}")
    if not request.query_params.get("code"):
        raise HTTPException(status_code=400, detail="Gmail authorization code was not provided.")
    try:
        complete_draft_authorization(
            authorization_response=str(request.url),
            db=db,
            user_id=int(os.getenv("AUTOAI_USER_ID", "1")),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Unable to save Gmail draft authorization: {error}"
        ) from error
    return {
        "status": "connected",
        "message": "Gmail is authorized for job-application draft creation. Trippie AutoAI will not send these drafts.",
    }


@router.get("/{user_id}")
def list_job_application_drafts(
    user_id: int, limit: int = 50, db: Session = Depends(get_db)
):
    rows = db.execute(
        select(JobEmailDraft, Job)
        .join(Job, Job.id == JobEmailDraft.job_id)
        .where(JobEmailDraft.user_id == user_id)
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
                "match_score": draft.match_score,
                "status": draft.status,
                "gmail_draft_id": draft.gmail_draft_id,
                "gmail_draft_url": draft.gmail_draft_url,
                "error": draft.error,
                "created_at": draft.created_at,
                "updated_at": draft.updated_at,
            }
            for draft, job in rows
        ],
    }

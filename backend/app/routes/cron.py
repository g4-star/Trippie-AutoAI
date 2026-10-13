from __future__ import annotations

import hmac
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import Settings
from app.services.discovery import discover_internet_jobs
from app.services.job_matcher import match_jobs_for_user
from app.services.job_application_drafts import create_job_application_drafts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cron", tags=["Scheduled Tasks"])


def _authorized(request: Request) -> bool:
    secret = os.getenv("CRON_SECRET", "")
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Scheduled task secret is not configured.",
        )

    supplied = request.headers.get("authorization", "")
    expected = f"Bearer {secret}"
    return hmac.compare_digest(supplied, expected)


@router.get("/job-drafts")
def scheduled_job_drafts(
    request: Request,
    db: Session = Depends(get_db),
):
    """Discover and match jobs, then create Gmail drafts only."""
    if not _authorized(request):
        raise HTTPException(status_code=401, detail="Unauthorized.")

    try:
        user_id = int(os.getenv("AUTOAI_USER_ID", "1"))
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail="AUTOAI_USER_ID must be an integer.",
        ) from exc

    settings = db.scalar(
        select(Settings).where(Settings.user_id == user_id)
    )

    if settings is None:
        raise HTTPException(
            status_code=409,
            detail="Agent settings have not been configured for this user.",
        )

    if not settings.agent_enabled:
        return {
            "status": "skipped",
            "reason": "The agent is disabled in settings.",
        }

    discovery = {
        "discovered": 0,
        "created": 0,
        "updated": 0,
        "failed": 0,
        "queries_run": 0,
    }

    if settings.automatic_job_discovery:
        try:
            discovery = discover_internet_jobs(
                db=db,
                user_id=user_id,
                queries_per_cycle=3,
                results_per_query=5,
            )
        except Exception:
            db.rollback()
            logger.exception("Scheduled job discovery failed.")
            raise HTTPException(
                status_code=502,
                detail="Job discovery failed; no draft cycle was completed.",
            )

    if os.getenv("AUTO_DRAFT_JOB_EMAILS", "true").strip().lower() not in {
        "1", "true", "yes", "on"
    }:
        return {
            "status": "skipped",
            "reason": "Job email drafts are disabled.",
            "discovery": {
                key: discovery.get(key, 0)
                for key in ("discovered", "created", "updated", "failed")
            },
        }

    try:
        matching = match_jobs_for_user(db=db, user_id=user_id)
        threshold = max(0, min(100, settings.minimum_match_score))
        eligible_matches = [
            match
            for match in matching.get("matches", [])
            if (match.get("score") or 0) >= threshold
        ]

        configured_limit = int(
            os.getenv(
                "JOB_EMAIL_DRAFT_DAILY_LIMIT",
                str(settings.daily_application_limit),
            )
        )
        # Bound the work per invocation and respect the user's configured limit.
        daily_limit = max(
            0,
            min(10, configured_limit, settings.daily_application_limit),
        )

        if daily_limit == 0:
            draft_result = {"created": 0, "failed": 0}
        else:
            draft_result = create_job_application_drafts(
                db=db,
                user_id=user_id,
                matches=eligible_matches,
                daily_limit=daily_limit,
            )

        return {
            "status": "completed",
            "discovery": {
                key: discovery.get(key, 0)
                for key in ("discovered", "created", "updated", "failed")
            },
            "jobs_analyzed": matching.get("jobs_analyzed", 0),
            "match_threshold": threshold,
            "eligible_matches": len(eligible_matches),
            "drafts": {
                "created": draft_result.get("created", 0),
                "failed": draft_result.get("failed", 0),
                "without_contact_email": draft_result.get(
                    "without_contact_email", 0
                ),
            },
            "email_sending": "manual in Gmail; this task does not send emails",
            "application_submission": "not performed",
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Scheduled job-draft cycle failed.")
        raise HTTPException(
            status_code=500,
            detail="Scheduled draft cycle failed. Check server logs.",
        )

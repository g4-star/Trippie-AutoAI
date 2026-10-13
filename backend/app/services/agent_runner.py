from __future__ import annotations

import logging
import os
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.email import Email
from app.models.settings import Settings
from app.services.agent_controller import is_agent_running
from app.services.application_engine import prepare_application
from app.services.discovery.discovery_engine import discover_internet_jobs
from app.services.job_application_drafts import create_job_application_drafts
from app.services.job_discovery import discover_and_save_jobs
from app.services.job_matcher import match_jobs_for_user
from app.services.gmail_service import sync_gmail
from app.services.reply_workflow import generate_pending_reply

logger = logging.getLogger(__name__)


def run_agent(*, db: Session, user_id: int) -> dict[str, Any]:
    """Run one cycle. Job application messages are saved as Gmail drafts only."""
    if not is_agent_running(db=db, user_id=user_id):
        return {"status": "stopped", "message": "AI Agent is stopped."}

    settings = db.scalar(select(Settings).where(Settings.user_id == user_id))
    if not settings:
        return {"status": "stopped", "message": "Agent settings were not found."}

    result: dict[str, Any] = {
        "status": "running",
        "jobs": {
            "discovered": 0, "created": 0, "updated": 0,
            "matched": 0, "applications_prepared": 0,
            "email_drafts_created": 0, "email_drafts_failed": 0,
            "without_contact_email": 0,
        },
        "email": {"synced": 0, "replies_generated": 0},
    }

    if settings.automatic_job_discovery and is_agent_running(db, user_id):
        try:
            discovery = discover_internet_jobs(
                db=db, user_id=user_id, queries_per_cycle=8, results_per_query=5
            )
        except Exception as error:
            logger.exception("Internet job discovery failed; trying legacy source: %s", error)
            discovery = discover_and_save_jobs(db=db, limit=20)
        result["jobs"]["discovered"] = discovery.get("discovered", 0)
        result["jobs"]["created"] = discovery.get("created", 0)
        result["jobs"]["updated"] = discovery.get("updated", 0)

    if not is_agent_running(db, user_id):
        result.update(status="stopped", message="Agent stopped during job discovery.")
        return result

    matching = match_jobs_for_user(db=db, user_id=user_id)
    matches = matching.get("matches", [])
    eligible_matches = [
        item for item in matches
        if int(item.get("score") or 0) >= settings.minimum_match_score
    ]
    result["jobs"]["matched"] = len(eligible_matches)

    # Application-email automation is strictly draft-only. It never calls a send endpoint.
    if is_agent_running(db, user_id):
        try:
            configured_limit = int(os.getenv(
                "JOB_EMAIL_DRAFT_DAILY_LIMIT", str(settings.daily_application_limit)
            ))
            draft_result = create_job_application_drafts(
                db=db,
                user_id=user_id,
                matches=eligible_matches,
                daily_limit=max(0, configured_limit),
            )
            result["jobs"]["email_drafts_created"] = draft_result.get("created", 0)
            result["jobs"]["email_drafts_failed"] = draft_result.get("failed", 0)
            result["jobs"]["without_contact_email"] = draft_result.get("without_contact_email", 0)
            result["job_email_drafts"] = draft_result
        except Exception as error:
            logger.exception("Job application draft cycle failed: %s", error)
            result["job_email_drafts"] = {"status": "failed", "error": str(error)[:500]}

    # Keep the existing application-preparation workflow; this prepares records only.
    if settings.automatic_application and is_agent_running(db, user_id):
        prepared_count = 0
        for match in eligible_matches:
            if not is_agent_running(db, user_id):
                break
            job_id = match.get("job_id")
            if not job_id:
                continue
            existing = db.scalar(
                select(Application).where(
                    Application.user_id == user_id, Application.job_id == job_id
                )
            )
            if existing:
                continue
            prepared = prepare_application(db=db, user_id=user_id, job_id=job_id)
            if prepared.get("success"):
                prepared_count += 1
            if prepared_count >= settings.daily_application_limit:
                break
        result["jobs"]["applications_prepared"] = prepared_count

    if not is_agent_running(db, user_id):
        result.update(status="stopped", message="Agent stopped during application processing.")
        return result

    if settings.email_monitoring and is_agent_running(db, user_id):
        email_result = sync_gmail(db=db, user_id=user_id, max_messages=50)
        result["email"]["synced"] = email_result.get("created", 0) + email_result.get("updated", 0)

    if not is_agent_running(db, user_id):
        result.update(status="stopped", message="Agent stopped during email processing.")
        return result

    if settings.email_monitoring and settings.auto_reply and is_agent_running(db, user_id):
        emails = db.scalars(select(Email).where(Email.user_id == user_id)).all()
        generated_count = 0
        for email in emails:
            if not is_agent_running(db, user_id):
                break
            generated = generate_pending_reply(user_id=user_id, email_id=email.id, db=db)
            if generated.get("status") == "pending_approval":
                generated_count += 1
        result["email"]["replies_generated"] = generated_count

    result["message"] = "AI Agent cycle completed. Job application emails were not sent."
    return result

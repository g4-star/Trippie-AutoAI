from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.email import Email
from app.models.settings import Settings
from app.services.agent_controller import is_agent_running
from app.services.application_engine import prepare_application
from app.services.application_submission import submit_application
from app.services.discovery import discover_internet_jobs
from app.services.job_application_drafts import create_job_application_drafts
from app.services.job_discovery import discover_and_save_jobs
from app.services.job_matcher import match_jobs_for_user
from app.services.gmail_service import sync_gmail
from app.services.reply_workflow import generate_pending_reply

logger = logging.getLogger(__name__)


def run_agent(*, db: Session, user_id: int) -> dict[str, Any]:
    """Run one agent cycle while preserving application and email safety checks."""

    if not is_agent_running(db=db, user_id=user_id):
        return {"status": "stopped", "message": "AI Agent is stopped."}

    settings = db.scalar(
        select(Settings).where(Settings.user_id == user_id)
    )
    if not settings:
        return {"status": "stopped", "message": "Agent settings were not found."}

    result: dict[str, Any] = {
        "status": "running",
        "jobs": {
            "discovered": 0,
            "created": 0,
            "updated": 0,
            "matched": 0,
            "applications_prepared": 0,
            "applications_submitted": 0,
            "applications_manual": 0,
            "applications_failed": 0,
            "email_drafts_created": 0,
            "email_drafts_failed": 0,
            "without_contact_email": 0,
        },
        "email": {"synced": 0, "replies_generated": 0},
    }

    # JOB DISCOVERY
    logger.info("Agent cycle: starting discovery for user %s", user_id)
    if settings.automatic_job_discovery and is_agent_running(db, user_id):
        try:
            discovery = discover_internet_jobs(
                db=db,
                user_id=user_id,
                queries_per_cycle=2,
                results_per_query=3,
            )
        except Exception:
            logger.exception("Internet discovery failed; trying the legacy source.")
            try:
                discovery = discover_and_save_jobs(db=db, limit=20)
            except Exception:
                logger.exception("Both job discovery sources failed.")
                discovery = {}

        logger.info("Agent cycle: discovery returned %s", discovery)
        for key in ("discovered", "created", "updated"):
            result["jobs"][key] = discovery.get(key, 0)

    if not is_agent_running(db, user_id):
        result.update(
            status="stopped",
            message="AI Agent stopped during job discovery.",
        )
        return result

    # MATCH JOBS USING THE EXISTING SKILLS-FIRST MATCHER.
    logger.info("Agent cycle: starting job matching for user %s", user_id)
    matching = match_jobs_for_user(db=db, user_id=user_id)
    logger.info("Agent cycle: matching finished for user %s", user_id)
    matches = matching.get("matches", [])
    eligible_matches = [
        match for match in matches
        if (match.get("score") or 0) >= settings.minimum_match_score
    ]
    result["jobs"]["matched"] = len(eligible_matches)

    # CREATE GMAIL DRAFTS. THIS DOES NOT SEND EMAILS.
    drafts_enabled = os.getenv("AUTO_DRAFT_JOB_EMAILS", "true").lower() in {
        "1", "true", "yes", "on"
    }

    if drafts_enabled and is_agent_running(db, user_id):
        try:
            try:
                draft_limit = int(os.getenv(
                    "JOB_EMAIL_DRAFT_DAILY_LIMIT",
                    str(settings.daily_application_limit),
                ))
            except ValueError:
                draft_limit = settings.daily_application_limit

            draft_result = create_job_application_drafts(
                db=db,
                user_id=user_id,
                matches=eligible_matches,
                daily_limit=max(0, draft_limit),
            )

            result["jobs"]["email_drafts_created"] = draft_result.get("created", 0)
            result["jobs"]["email_drafts_failed"] = draft_result.get("failed", 0)
            result["jobs"]["without_contact_email"] = (
                draft_result.get("without_contact_email", 0)
            )
            result["job_email_drafts"] = draft_result

        except Exception as error:
            logger.exception("Job application draft cycle failed.")
            result["job_email_drafts"] = {
                "status": "failed",
                "error": str(error)[:500],
            }

    if not is_agent_running(db, user_id):
        result.update(
            status="stopped",
            message="AI Agent stopped during job-draft processing.",
        )
        return result

    # APPLICATION PREPARATION AND EXISTING SUBMISSION WORKFLOW.
    # Enforce the daily cap across repeated worker cycles, not just within
    # one cycle. Every created application record counts as an attempt, even
    # when the provider requires manual action or submission later fails.
    today_start = datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    applications_today = db.scalar(
        select(func.count(Application.id)).where(
            Application.user_id == user_id,
            Application.created_at >= today_start,
        )
    ) or 0
    remaining_daily_applications = max(
        0,
        int(settings.daily_application_limit) - int(applications_today),
    )

    if settings.automatic_application and is_agent_running(db, user_id):
        prepared_count = 0

        for match in eligible_matches:
            if prepared_count >= remaining_daily_applications:
                break
            if not is_agent_running(db, user_id):
                break

            job_id = match.get("job_id")
            if not job_id:
                continue

            existing = db.scalar(
                select(Application).where(
                    Application.user_id == user_id,
                    Application.job_id == job_id,
                )
            )
            if existing:
                continue

            prepared = prepare_application(
                db=db,
                user_id=user_id,
                job_id=job_id,
            )
            if not prepared.get("success"):
                continue

            prepared_count += 1
            application_id = prepared.get("application_id")
            if not application_id:
                continue

            submission = submit_application(
                db=db,
                application_id=application_id,
            )
            status = submission.get("status")

            if status == "submitted":
                result["jobs"]["applications_submitted"] += 1
            elif status == "manual_action_required":
                result["jobs"]["applications_manual"] += 1
            elif status == "submission_failed":
                result["jobs"]["applications_failed"] += 1

        result["jobs"]["applications_prepared"] = prepared_count
        result["jobs"]["daily_limit"] = int(settings.daily_application_limit)
        result["jobs"]["applications_created_today_before_cycle"] = int(applications_today)

    if not is_agent_running(db, user_id):
        result.update(
            status="stopped",
            message="AI Agent stopped during application processing.",
        )
        return result

    logger.info("Agent cycle: reaching Gmail stage for user %s", user_id)
    # GMAIL MONITORING. Gmail authentication/network errors must not
    # abort job discovery and matching.
    if settings.email_monitoring and is_agent_running(db, user_id):
        try:
            logger.info("Agent cycle: starting Gmail sync for user %s", user_id)
            email_result = sync_gmail(
                db=db,
                user_id=user_id,
                max_messages=50,
            )
            result["email"]["synced"] = (
                email_result.get("created", 0)
                + email_result.get("updated", 0)
            )
            result["email"]["status"] = "ok"
            logger.info("Agent cycle: Gmail sync finished for user %s", user_id)
        except Exception as error:
            logger.exception("Gmail sync failed; continuing agent cycle.")
            result["email"]["status"] = "error"
            result["email"]["error"] = str(error)[:300]

    if not is_agent_running(db, user_id):
        result.update(
            status="stopped",
            message="AI Agent stopped during email processing.",
        )
        return result

    # EXISTING EMAIL REPLY WORKFLOW.
    if (
        settings.email_monitoring
        and settings.auto_reply
        and is_agent_running(db, user_id)
    ):
        emails = db.scalars(
            select(Email).where(Email.user_id == user_id)
        ).all()

        generated_count = 0
        for email in emails:
            if not is_agent_running(db, user_id):
                break

            generated = generate_pending_reply(
                user_id=user_id,
                email_id=email.id,
                db=db,
            )
            if generated.get("status") == "pending_approval":
                generated_count += 1

        result["email"]["replies_generated"] = generated_count

    result["message"] = (
        "AI Agent cycle completed. "
        f"Prepared: {result['jobs']['applications_prepared']}, "
        f"Submitted: {result['jobs']['applications_submitted']}, "
        f"Manual action: {result['jobs']['applications_manual']}, "
        f"Failed: {result['jobs']['applications_failed']}, "
        f"Job email drafts created: {result['jobs']['email_drafts_created']}. "
        "Job application emails are drafted, not automatically sent."
    )
    return result

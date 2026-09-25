from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job import Job
from app.models.settings import Settings
from app.services.agent_controller import is_agent_running
from app.services.application_engine import prepare_application
from app.services.gmail_service import sync_gmail
from app.services.job_discovery import discover_and_save_jobs
from app.services.job_matcher import match_jobs_for_user
from app.services.reply_workflow import generate_pending_reply


def run_agent(
    *,
    db: Session,
    user_id: int,
) -> dict[str, Any]:
    """
    Run one automation cycle for a user.

    The agent checks its master switch before every major operation.
    It never bypasses the existing email safety/approval workflow.
    """

    if not is_agent_running(
        db=db,
        user_id=user_id,
    ):
        return {
            "status": "stopped",
            "message": "AI Agent is stopped.",
        }

    settings = db.scalar(
        select(Settings).where(
            Settings.user_id == user_id
        )
    )

    if not settings:
        return {
            "status": "stopped",
            "message": "Agent settings were not found.",
        }

    result: dict[str, Any] = {
        "status": "running",
        "jobs": {
            "discovered": 0,
            "created": 0,
            "updated": 0,
            "matched": 0,
            "applications_prepared": 0,
        },
        "email": {
            "synced": 0,
            "replies_generated": 0,
        },
    }

    # ---------------------------------------------------------
    # JOB DISCOVERY
    # ---------------------------------------------------------

    if (
        settings.automatic_job_discovery
        and is_agent_running(db, user_id)
    ):
        discovery = discover_and_save_jobs(
            db=db,
            limit=20,
        )

        result["jobs"]["discovered"] = discovery.get(
            "discovered",
            0,
        )
        result["jobs"]["created"] = discovery.get(
            "created",
            0,
        )
        result["jobs"]["updated"] = discovery.get(
            "updated",
            0,
        )

    if not is_agent_running(db, user_id):
        result["status"] = "stopped"
        result["message"] = "AI Agent stopped during job processing."
        return result

    # ---------------------------------------------------------
    # JOB MATCHING
    # ---------------------------------------------------------

    matching = match_jobs_for_user(
        db=db,
        user_id=user_id,
    )

    matches = matching.get(
        "matches",
        [],
    )

    eligible_matches = [
        match
        for match in matches
        if (
            (match.get("score") or 0)
            >= settings.minimum_match_score
        )
    ]

    result["jobs"]["matched"] = len(
        eligible_matches
    )

    # ---------------------------------------------------------
    # APPLICATION PREPARATION
    # ---------------------------------------------------------

    if (
        settings.automatic_application
        and is_agent_running(db, user_id)
    ):
        prepared_count = 0

        for match in eligible_matches:
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

            if prepared.get("success"):
                prepared_count += 1

            if prepared_count >= settings.daily_application_limit:
                break

        result["jobs"]["applications_prepared"] = (
            prepared_count
        )

    if not is_agent_running(db, user_id):
        result["status"] = "stopped"
        result["message"] = "AI Agent stopped during application processing."
        return result

    # ---------------------------------------------------------
    # GMAIL MONITORING
    # ---------------------------------------------------------

    if (
        settings.email_monitoring
        and is_agent_running(db, user_id)
    ):
        email_result = sync_gmail(
            db=db,
            user_id=user_id,
            max_messages=50,
        )

        result["email"]["synced"] = (
            email_result.get("created", 0)
            + email_result.get("updated", 0)
        )

    if not is_agent_running(db, user_id):
        result["status"] = "stopped"
        result["message"] = "AI Agent stopped during email processing."
        return result

    # ---------------------------------------------------------
    # EMAIL REPLY GENERATION
    # ---------------------------------------------------------
    #
    # This generates drafts for eligible emails.
    # Actual sending remains controlled by the existing
    # reply decision and approval system.
    #
    # Automatic sending will only be added for routine
    # categories when auto_reply is explicitly enabled.

    if (
        settings.email_monitoring
        and settings.auto_reply
        and is_agent_running(db, user_id)
    ):
        emails = db.execute(
            select(
                __import__(
                    "app.models.email",
                    fromlist=["Email"],
                ).Email
            ).where(
                __import__(
                    "app.models.email",
                    fromlist=["Email"],
                ).Email.user_id == user_id
            )
        ).scalars().all()

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

        result["email"]["replies_generated"] = (
            generated_count
        )

    result["message"] = "AI Agent cycle completed."

    return result

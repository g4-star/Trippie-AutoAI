from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job import Job


SUPPORTED_AUTOMATED_SOURCES = {
    # Add providers here only when we have an authorized
    # API/integration for their application submission flow.
}


def _submission_method(job: Job) -> str:
    source = (job.source or "").strip().lower()

    if source in {
        item.lower()
        for item in SUPPORTED_AUTOMATED_SOURCES
    }:
        return "automated"

    return "manual"


def submit_application(
    *,
    db: Session,
    application_id: int,
) -> dict[str, Any]:
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        return {
            "success": False,
            "status": "not_found",
            "error": "Application not found.",
        }

    job = db.get(
        Job,
        application.job_id,
    )

    if not job:
        return {
            "success": False,
            "status": "submission_failed",
            "error": "Job not found.",
        }

    if application.status == "submitted":
        return {
            "success": True,
            "status": "submitted",
            "message": "Application has already been submitted.",
            "application_id": application.id,
            "submitted_at": application.submitted_at,
        }

    if application.status in {
        "rejected",
        "withdrawn",
    }:
        return {
            "success": False,
            "status": "manual_action_required",
            "error": (
                f"Application cannot be submitted while its "
                f"status is '{application.status}'."
            ),
        }

    method = _submission_method(job)

    # ---------------------------------------------------------
    # AUTOMATED SUBMISSION
    # ---------------------------------------------------------
    #
    # Only providers with an explicitly implemented and
    # authorized submission adapter belong here.
    #
    # We intentionally do not submit arbitrary HTML forms,
    # automate third-party logins, solve CAPTCHAs, or bypass
    # MFA / anti-bot controls.
    #

    if method == "automated":
        return _submit_with_authorized_adapter(
            db=db,
            application=application,
            job=job,
        )

    # ---------------------------------------------------------
    # MANUAL SUBMISSION
    # ---------------------------------------------------------

    application.status = "manual_action_required"
    application.updated_at = datetime.utcnow()

    application.notes = (
        (application.notes or "")
        + "\n\n"
        "Submission requires user action on the official "
        "application website. TrippieAutoAI did not claim "
        "that the application was submitted."
    )

    db.commit()
    db.refresh(application)

    return {
        "success": False,
        "status": "manual_action_required",
        "application_id": application.id,
        "job_id": job.id,
        "application_url": job.job_url,
        "source": job.source,
        "message": (
            "This application source does not currently have "
            "an authorized automated submission adapter."
        ),
    }


def _submit_with_authorized_adapter(
    *,
    db: Session,
    application: Application,
    job: Job,
) -> dict[str, Any]:
    """
    Placeholder for explicitly authorized provider adapters.

    A provider adapter must return success only after it receives
    a genuine successful submission response from the provider.
    """

    application.status = "submission_failed"
    application.updated_at = datetime.utcnow()

    application.notes = (
        (application.notes or "")
        + "\n\n"
        "Automated submission adapter is not implemented for "
        f"source '{job.source}'."
    )

    db.commit()
    db.refresh(application)

    return {
        "success": False,
        "status": "submission_failed",
        "application_id": application.id,
        "job_id": job.id,
        "source": job.source,
        "error": (
            "No authorized submission adapter is implemented "
            "for this source."
        ),
    }

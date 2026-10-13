from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_email_draft import JobEmailDraft
from app.models.user import User
from app.services.gmail_draft_service import create_gmail_draft
from app.services.job_matcher import calculate_match


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
IGNORED_EMAIL_PARTS = ("noreply", "no-reply", "donotreply", "example.com", "test.com")


def _recipient_for(job: Job) -> str | None:
    source_text = "\n".join(value for value in (job.description, job.requirements) if value)
    for candidate in EMAIL_PATTERN.findall(source_text):
        email = candidate.strip(".,;:()[]{}<>").lower()
        if any(part in email for part in IGNORED_EMAIL_PARTS):
            continue
        return email
    return None


def _make_email(user: User, job: Job, match: dict[str, Any]) -> tuple[str, str]:
    title = (job.title or "the advertised role").strip()
    company = (job.company or "your organization").strip()
    skills = match.get("skill_matches") or []
    skill_text = ", ".join(str(skill) for skill in skills[:6] if skill)
    if not skill_text:
        skill_text = "my current technical skills and hands-on project work"

    subject = f"Application: {title} — {user.full_name}"
    portfolio = os.getenv("PORTFOLIO_URL", "https://dickson-kiprono.vercel.app")
    linkedin = "https://www.linkedin.com/in/dickson-sang-265737386/"
    github = "https://github.com/g4-star"
    body = (
        f"Dear Hiring Team,\n\n"
        f"I am writing to apply for the {title} opportunity at {company}. "
        f"After reviewing the role, I believe my practical skills in {skill_text} "
        f"are relevant to the work described.\n\n"
        f"My approach is to demonstrate capability through hands-on work, projects, "
        f"problem-solving, and outcomes—not to rely on degree titles alone. I am "
        f"ready to demonstrate relevant work, learn your team's processes, and be "
        f"transparent about the experience and skills I currently have.\n\n"
        f"My portfolio, including my projects and professional profile, is available here:\n"
        f"Portfolio: {portfolio}\nGitHub: {github}\nLinkedIn: {linkedin}\n\n"
        f"I would appreciate the opportunity to discuss how I could contribute to "
        f"{company}. Thank you for your time and consideration.\n\n"
        f"Kind regards,\n{user.full_name}\n{user.email}"
        + (f"\n{user.phone}" if user.phone else "")
    )
    return subject, body


def create_job_application_drafts(
    *,
    db: Session,
    user_id: int,
    matches: list[dict[str, Any]],
    daily_limit: int = 10,
) -> dict[str, Any]:
    """Create Gmail drafts only for matched jobs with a contact email in the listing."""
    enabled = os.getenv("AUTO_DRAFT_JOB_EMAILS", "true").strip().lower()
    if enabled in {"0", "false", "no", "off"}:
        return {"status": "disabled", "created": 0, "skipped": 0, "failed": 0}

    user = db.get(User, user_id)
    if not user:
        return {"status": "skipped", "reason": "profile_not_found", "created": 0}

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    created_today = db.scalar(
        select(func.count(JobEmailDraft.id)).where(
            JobEmailDraft.user_id == user_id,
            JobEmailDraft.status == "created",
            JobEmailDraft.created_at >= today,
        )
    ) or 0
    remaining = max(0, int(daily_limit) - int(created_today))
    created = skipped = failed = no_contact = 0
    errors: list[str] = []

    for item in matches:
        if remaining <= 0:
            break
        job_id = item.get("job_id")
        score = int(item.get("score") or 0)
        if not job_id:
            skipped += 1
            continue
        job = db.get(Job, int(job_id))
        if not job or not job.is_active:
            skipped += 1
            continue

        existing = db.scalar(
            select(JobEmailDraft).where(
                JobEmailDraft.user_id == user_id,
                JobEmailDraft.job_id == job.id,
            )
        )
        if existing and existing.status == "created" and existing.gmail_draft_id:
            skipped += 1
            continue

        recipient = _recipient_for(job)
        if not recipient:
            no_contact += 1
            continue

        match = calculate_match(job=job, user=user)
        subject, body = _make_email(user, job, match)
        if existing is None:
            existing = JobEmailDraft(
                user_id=user_id, job_id=job.id, recipient_email=recipient,
                subject=subject, body=body, match_score=score, status="pending",
            )
            db.add(existing)
        else:
            existing.recipient_email = recipient
            existing.subject = subject
            existing.body = body
            existing.match_score = score
            existing.status = "pending"
            existing.error = None
        db.commit()
        db.refresh(existing)

        try:
            result = create_gmail_draft(
                db=db, user_id=user_id, to=recipient, subject=subject, body=body
            )
            existing.gmail_draft_id = result["draft_id"]
            existing.gmail_draft_url = result["url"]
            existing.status = "created"
            existing.error = None
            existing.updated_at = datetime.utcnow()
            db.commit()
            created += 1
            remaining -= 1
        except Exception as error:
            db.rollback()
            failed += 1
            message = str(error)[:1000]
            errors.append(f"{job.company} — {job.title}: {message}")
            retry_record = db.scalar(
                select(JobEmailDraft).where(
                    JobEmailDraft.user_id == user_id,
                    JobEmailDraft.job_id == job.id,
                )
            )
            if retry_record:
                retry_record.status = "failed"
                retry_record.error = message
                retry_record.updated_at = datetime.utcnow()
                db.commit()

    return {
        "status": "completed",
        "created": created,
        "skipped": skipped,
        "without_contact_email": no_contact,
        "failed": failed,
        "remaining_daily_capacity": remaining,
        "errors": errors[:5],
    }

from __future__ import annotations

import html
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
from app.services.sms_notification_service import notify_job_draft_ready


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


def _make_email(user: User, job: Job, match: dict[str, Any]) -> tuple[str, str, str]:
    title = (job.title or "the advertised role").strip()
    company = (job.company or "your organization").strip()
    skills = match.get("skill_matches") or []
    skill_text = ", ".join(str(skill) for skill in skills[:6] if skill)
    if not skill_text:
        skill_text = "my current technical skills and hands-on project work"

    subject = f"Application: {title} — {user.full_name}"
    portfolio = os.getenv("PORTFOLIO_URL", "https://dickson-kiprono.vercel.app").rstrip("/")
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
    safe_title, safe_company = html.escape(title), html.escape(company)
    safe_name = html.escape(user.full_name or "Dickson Kiprono")
    safe_skills = html.escape(skill_text)
    safe_email = html.escape(user.email or "")
    safe_phone = html.escape(user.phone or "")
    html_body = f"""
<!doctype html><html><body style="font-family:Arial,Helvetica,sans-serif;color:#202124;line-height:1.6">
<p>Dear Hiring Team,</p>
<p>I am writing to apply for the <strong>{safe_title}</strong> opportunity at {safe_company}.
After reviewing the role, I believe my practical skills in {safe_skills} are relevant to the work described.</p>
<p>My approach is to demonstrate capability through hands-on work, projects, problem-solving, and outcomes—not to rely on degree titles alone. I am ready to demonstrate relevant work, learn your team's processes, and be transparent about the experience and skills I currently have.</p>
<p>My portfolio and professional profiles are available here:</p>
<ul>
<li><a href="{html.escape(portfolio, quote=True)}" target="_blank" rel="noopener noreferrer">View my Portfolio</a></li>
<li><a href="{html.escape(github, quote=True)}" target="_blank" rel="noopener noreferrer">View my GitHub projects</a></li>
<li><a href="{html.escape(linkedin, quote=True)}" target="_blank" rel="noopener noreferrer">View my LinkedIn profile</a></li>
</ul>
<p>I would appreciate the opportunity to discuss how I could contribute to {safe_company}. Thank you for your time and consideration.</p>
<p>Kind regards,<br><strong>{safe_name}</strong><br>{safe_email}<br>{safe_phone}</p>
</body></html>
""".strip()
    return subject, body, html_body


def create_job_application_drafts(
    *, db: Session, user_id: int, matches: list[dict[str, Any]], daily_limit: int = 10
) -> dict[str, Any]:
    """Create Gmail drafts only; after creation, notify the owner by SMS if configured."""
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
    created = skipped = failed = no_contact = notified = notification_failed = 0
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
                JobEmailDraft.user_id == user_id, JobEmailDraft.job_id == job.id
            )
        )
        if existing and existing.status == "created" and existing.gmail_draft_id:
            # Retry notification only if draft exists but SMS had not been queued.
            if not existing.notification_sent and existing.gmail_draft_url:
                ok, error = notify_job_draft_ready(
                    job_title=job.title, company=job.company, match_score=existing.match_score,
                    gmail_draft_url=existing.gmail_draft_url,
                )
                if ok:
                    existing.notification_sent = True
                    existing.notification_error = None
                    notified += 1
                elif error and not error.startswith("SMS not configured"):
                    existing.notification_error = error
                    notification_failed += 1
                db.commit()
            skipped += 1
            continue

        recipient = _recipient_for(job)
        if not recipient:
            no_contact += 1
            continue

        match = calculate_match(job=job, user=user)
        subject, body, body_html = _make_email(user, job, match)
        if existing is None:
            existing = JobEmailDraft(
                user_id=user_id, job_id=job.id, recipient_email=recipient,
                subject=subject, body=body, body_html=body_html,
                match_score=score, status="pending",
            )
            db.add(existing)
        else:
            existing.recipient_email = recipient
            existing.subject = subject
            existing.body = body
            existing.body_html = body_html
            existing.match_score = score
            existing.status = "pending"
            existing.error = None
        db.commit()
        db.refresh(existing)

        try:
            result = create_gmail_draft(
                db=db, user_id=user_id, to=recipient, subject=subject,
                body=body, body_html=body_html,
            )
            existing.gmail_draft_id = result["draft_id"]
            existing.gmail_draft_url = result["url"]
            existing.status = "created"
            existing.error = None
            existing.updated_at = datetime.utcnow()
            db.commit()
            created += 1
            remaining -= 1

            ok, error = notify_job_draft_ready(
                job_title=job.title, company=job.company, match_score=score,
                gmail_draft_url=result["url"],
            )
            if ok:
                existing.notification_sent = True
                existing.notification_error = None
                notified += 1
            elif error and not error.startswith("SMS not configured"):
                existing.notification_error = error
                notification_failed += 1
            db.commit()
        except Exception as error:
            db.rollback()
            failed += 1
            message = str(error)[:1000]
            errors.append(f"{job.company} — {job.title}: {message}")
            retry_record = db.scalar(
                select(JobEmailDraft).where(
                    JobEmailDraft.user_id == user_id, JobEmailDraft.job_id == job.id
                )
            )
            if retry_record and not retry_record.gmail_draft_id:
                retry_record.status = "failed"
                retry_record.error = message
                retry_record.updated_at = datetime.utcnow()
                db.commit()

    return {
        "status": "completed", "created": created, "skipped": skipped,
        "without_contact_email": no_contact, "failed": failed,
        "sms_notifications_queued": notified,
        "sms_notifications_failed": notification_failed,
        "remaining_daily_capacity": remaining, "errors": errors[:5],
    }

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.services.job_matcher import calculate_match


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def _build_cover_letter(
    user: User,
    job: Job,
    match: dict[str, Any],
) -> str:
    matched_skills = match.get("skill_matches", [])
    missing_skills = match.get("missing_skills", [])

    skill_text = ", ".join(matched_skills[:6])

    if skill_text:
        opening = (
            f"I am interested in the {job.title} opportunity at "
            f"{job.company}. My background and hands-on skills in "
            f"{skill_text} align with several of the technical "
            f"requirements of this role."
        )
    else:
        opening = (
            f"I am interested in the {job.title} opportunity at "
            f"{job.company} and would welcome the opportunity to "
            f"contribute my technical skills to your team."
        )

    body = (
        "I am particularly motivated by opportunities where I can "
        "apply my existing technical knowledge while continuing to "
        "learn and grow. I bring determination, a strong work ethic, "
        "adaptability, and a willingness to learn new technologies "
        "and processes required by the role."
    )

    closing = (
        "While I may not meet every requirement listed in the "
        "description, I believe my existing skills, willingness to "
        "learn, flexibility, and commitment to delivering quality "
        "work would allow me to contribute positively to the team. "
        "I would appreciate the opportunity to demonstrate my "
        "capabilities and discuss how I can grow into the role."
    )

    return (
        f"Dear Hiring Team,\n\n"
        f"{opening}\n\n"
        f"{body}\n\n"
        f"{closing}\n\n"
        f"Kind regards,\n"
        f"{user.full_name}\n"
        f"{user.email}"
    )


def prepare_application(
    db: Session,
    user_id: int,
    job_id: int,
) -> dict[str, Any]:
    user = db.get(User, user_id)
    job = db.get(Job, job_id)

    if not user:
        return {
            "success": False,
            "error": "User not found.",
        }

    if not job:
        return {
            "success": False,
            "error": "Job not found.",
        }

    existing = db.scalar(
        select(Application)
        .where(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )
    )

    if existing:
        return {
            "success": False,
            "error": "An application already exists for this job.",
            "application_id": existing.id,
            "status": existing.status,
        }

    match = calculate_match(
        job=job,
        user=user,
    )

    cover_letter = _build_cover_letter(
        user=user,
        job=job,
        match=match,
    )

    notes = (
        f"Match score: {match['score']}%.\n"
        f"Matched skills: "
        f"{', '.join(match['skill_matches']) or 'None'}.\n"
        f"Missing skills: "
        f"{', '.join(match['missing_skills']) or 'None'}.\n"
        f"Education requirement: "
        f"{match['education_requirements'] or 'Not specified'}.\n"
        f"Experience requirement: "
        f"{match['experience_requirements'] or 'Not specified'}.\n"
        "Education and experience requirements are informational "
        "and were not used as negative scoring criteria."
    )

    application = Application(
        user_id=user_id,
        job_id=job_id,
        status="prepared",
        match_score=match["score"],
        cover_letter=cover_letter,
        notes=notes,
        application_url=job.job_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "success": True,
        "application_id": application.id,
        "status": application.status,
        "match_score": application.match_score,
        "job": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "application_url": job.job_url,
        },
        "matched_skills": match["skill_matches"],
        "missing_skills": match["missing_skills"],
        "education_requirements": match["education_requirements"],
        "experience_requirements": match["experience_requirements"],
        "cover_letter": cover_letter,
        "notes": notes,
    }
